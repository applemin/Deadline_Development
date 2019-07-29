# -*- coding: utf-8 -*-

"""
deadline_submission.parse_output

Module that handles parsing Deadline command submission output
"""

import re
import sys

__all__ = (
    'DeadlineSubmissionOutput',
    'ParseSubmissionOutputError',
)


class ParseSubmissionOutputError(RuntimeError):
    """Exception indicating a parser error"""
    def __init__(self, msg, line):
        super(ParseSubmissionOutputError, self).__init__()
        self.msg = msg
        self.line = line

    def __str__(self):
        s = "ParseSubmissionOutputError: " + self.msg
        if self.line:
            s += " (" + self.line + ")"
        else:
            s += " [NO LINE]"
        return s


class _DeadlineSubmissionError(Exception):
    """
    Special flow-control exception for dealing with error messages while parsing the submission output. Error messages
    can occur during any state. This is to allow a general mechanism to short circuit the regular state-machine
    processing when reading lines from the iterator.
    """
    def __init__(self, result, error_msg):
        self.result = result
        self.error_msg = error_msg


class DeadlineSubmissionOutput(object):
    """Class that handles parsing standard output from DeadlineCommand submission"""

    # Regex for capturing Deadline version
    RE_DEADLINE_VERSION = re.compile(
        r"^Deadline Command(?: BG)? \d+\.\d+ "
        r"\[v(?P<version>\d+(?:\.\d+){3}) Release \((?P<git_sha>[a-f0-9]{9})\)\]$"
    )
    # Regex for capturing repository location
    RE_REPOSITORY = re.compile(
        r"^Submitting to Repository: (?P<repository>.*)$"
    )
    # Regexes for handling error messages
    RE_ERRORS = (
        re.compile(
            r'^(?P<result>(?:Submission )?Error): (?P<error_msg>.*)$'
        ),
        re.compile(
            r'^(?P<error_msg>Bad submission arguments)$'
        )
    )
    DEFAULT_ERROR_RESULT = "Error"
    # Regex pattern for an auxiliary file listing
    RE_AUX_FILE_LISTING = re.compile(
        r"^\d+\) (?P<path>.*)$"
    )
    # Output line indicating auxiliary files begin below
    AUX_FILES_LINE = "Submission Contains the Following Auxiliary Files:"
    # Output line indicating no auxiliary files submitted
    NO_AUX_FILES_LINE = "Submission Contains No Auxiliary Files."
    # Output line indicating submission warnings begin below
    RE_CHECK_WARNINGS = re.compile(
        r"^The job was submitted successfully(?:\.|, but there were some (?P<warnings>warnings):)$"
    )
    # A mapping of the keys from the submission output to object attributes
    KEY_ATTR_MAPPING = {
        "JobID": "job_id",
        "Result": "result"
    }
    # The final state
    STATE_DONE = "DONE"

    def __init__(self, output):
        """
        Creates an instance of DeadlineSubmissionOutput based on a string containing the standard output emitted by
        DeadlineCommand when submitting a job.
        """

        # Input validation
        string_types = (str, unicode) if sys.version_info[0] == 2 else str
        if not isinstance(output, string_types):
            raise TypeError("output must be a string")

        # Initialize the state
        self.version = None
        self.repository = None
        self.result = None
        self.job_id = None
        self.error = None
        self.warnings = []
        self.aux_files = []

        # Perform the parsing
        self._parse(output)

    def _read_line(self, required=True):
        """
        Reads a line from the line iterator. Can optionally handle early EOF by passing required=True. Also handles
        parsing error message lines since they can occur during any state of the parsing state machine

        :param required:    Optional bool (default True) indicating whether the line is required by parsing. If a
                            StopIteration is raised, this raises a ParseSubmissionOutputError up to the caller
        :raises ParseSubmissionOutputError: When required is True and there are not more lines to read
        :return:            The line or None if required is False and there are no further lines
        """

        line = None
        try:
            line = next(self._it)
            # Check the line against error regular expressions
            for re_error in self.RE_ERRORS:
                match = re_error.search(line)
                if match:
                    groups = match.groupdict()
                    raise _DeadlineSubmissionError(
                        result=groups.get("result", self.DEFAULT_ERROR_RESULT),
                        error_msg=groups["error_msg"]
                    )
        except StopIteration:
            if required:
                raise ParseSubmissionOutputError("Unexpected EOF", None)
        return line

    def _parse(self, output):
        """
        Parse the standard output emitted from DeadlineCommand when attempting to submit a job.

        This is implemented as a state machine. The state is the instance method that should be run.

        :param output: The output emitted by DeadlineCommand when attempting to submit a job
        """

        state = self._parse_version
        self._it = iter(output.splitlines())

        try:
            while state != self.STATE_DONE:
                state = state()
        except _DeadlineSubmissionError as e:
            # Encountered an error message so we are done
            self.result = e.result
            self.error = e.error_msg
            try:
                line = next(self._it)
            except StopIteration:
                # The error message should be the last line in the output
                # If not, we are not handling the output correctly
                pass
            else:
                raise ParseSubmissionOutputError("Expected EOF", line)

    def _parse_version(self):
        """Parses the DeadlineCommand version line (the first line)"""

        line = self._read_line()
        match = self.RE_DEADLINE_VERSION.search(line)
        if not match:
            raise ParseSubmissionOutputError("Expected version line", line)
        self.version = tuple(int(c) for c in match.group('version').split('.'))
        return self._parse_repository

    def _parse_repository(self):
        """Parses the blank line following the version line and the line indicating the repository being used"""
        # Should be a blank line
        line = self._read_line()
        if line != "":
            raise ParseSubmissionOutputError("Expected a blank line", line)

        # Next line should match the repository line pattern
        line = self._read_line()
        match = self.RE_REPOSITORY.search(line)
        if not match:
            raise ParseSubmissionOutputError("Missing repository line", line)
        # Extract the information
        self.repository = match.group("repository")

        return self._parse_auxiliary_files

    def _parse_auxiliary_files(self):
        """
        Parses:
            - the blank line following the repository line
            - subsequent lines regarding auxiliary files
            - the blank line that follows
        """

        # Blank line
        line = self._read_line()
        if line != "":
            raise ParseSubmissionOutputError("Expected blank line", line)

        line = self._read_line()
        if line == self.AUX_FILES_LINE:
            # Auxiliary files included
            line = self._read_line()
            # Take auxiliary files until we get a blank line
            while line != "":
                match = self.RE_AUX_FILE_LISTING.search(line)
                if not match:
                    raise ParseSubmissionOutputError("Expected auxiliary file listing", line)
                self.aux_files.append(match.group("path"))
                line = self._read_line()
        elif line == self.NO_AUX_FILES_LINE:
            # Has no auxiliary files
            # Handle blank line
            line = self._read_line()
            if line != "":
                raise ParseSubmissionOutputError("Expected blank line", line)

        return self._parse_key_value_pairs

    def _parse_key_value_pairs(self):
        """
        Parses the key-value pair lines separated by an equal sign (=) and the blank line that follows
        """
        line = self._read_line()
        # Until we get a blank line
        while line != "":
            key, value = line.split("=", 1)
            attr = self.KEY_ATTR_MAPPING.get(key, None)
            if attr:
                setattr(self, attr, value)
            line = self._read_line()

        return self._parse_warning_check

    def _parse_warning_check(self):
        """
        Parses the line that potentially indicates there were submission warnings. If so, handles subsequent lines
        """
        line = self._read_line(required=False)
        if line is not None:
            # Match the pattern
            match = self.RE_CHECK_WARNINGS.search(line)
            if match:
                # If we detect the warning clause, collect the lines that follow into the warning list
                if match.group("warnings"):
                    line = self._read_line()
                    # Loop until the end of the file
                    while line is not None:
                        self.warnings.append(line)
                        line = self._read_line(required=False)
            else:
                raise ParseSubmissionOutputError("Unexpected line", line)
        return self.STATE_DONE
