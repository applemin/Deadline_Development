from __future__ import print_function, unicode_literals

import io
import os
import re

class IFLParser:
    # ie. "this_is_my_file_00001.tga 20" where 20 is the optional frame arg. Assumes comments are removed.
    remove_frame_regex = re.compile(r'(.*)\s\d+$')


    def __init__(self, ifl):
        self.ifl = ifl
        self.parsed_files = []


    def getFilesInIFL(self):
        """
        The main function in the IFLParser called to retrieve a list of full file paths for entries in an IFL
        returns a list of files
        :return: Returns a sorted list of unique files listed from the IFL.
        """
        self.parsed_files = []
        ifl_directory = os.path.dirname(self.ifl)
        with io.open(self.ifl, 'r', encoding='utf-8') as file_handle:
            for line in file_handle:
                line = self.removeCommentsAndTrimLine(line)
                # continue early if there was only a comment or nothing on the line
                if not line:
                    continue

                # Now we need to check if there's an optional frame argument
                potential_files = self.removeFrameArgFromLine(line)

                # We need the full file path to add it to our list of confirmed files
                file_in_ifl = self.getValidatedFilePath(potential_files, ifl_directory)
                if file_in_ifl:
                    self.parsed_files.append(file_in_ifl)

        self.parsed_files = sorted(list(set(self.parsed_files)))
        return self.parsed_files


    @staticmethod
    def removeCommentsAndTrimLine(line):
        """
        # Remove the comments from a line in an .ifl file
        :param line: A singular line in an .ifl file
        :return: Returns line with the comments removed and trimmed whitespace
        """
        line = line.strip()
        if not line or line.startswith(";"):
            return ''

        # Find the first semi-colon and remove it (and everything to right of it) from the line
        index = line.find(";")
        if index >= 0:
            return line[:index].strip()
        return line


    @classmethod
    def removeFrameArgFromLine(cls, line):
        """
        Get the potential paths from a line in an .ifl file by searching for the optional frame argument
        :param line: A singular line in an .ifl file, with any comments already removed
        :return: Returns a file path with the optional frame argument removed.
        """
        line = line.strip()
        # Try to determine if there's an optional frame argument on the line
        file_before_frame = cls.remove_frame_regex.match(line)
        if file_before_frame:
            return file_before_frame.group(1).strip()
        return line


    @staticmethod
    def getValidatedFilePath(file_path, ifl_directory):
        """
         Returns the validated filepath for the file. We don't know if the path is the full file
         path or just the filename, we need to figure out the full file path by first checking the entry in the IFL,
         followed by joining it with the IFL's directory.
        :param file_path: A potential file path we need to validate its existence
        :param ifl_directory: The directory of the .ifl file to parse
        :return: Returns a validated file path if it exists, otherwise returns None
        """

        if os.path.isfile(file_path):
            return file_path
        elif os.path.isfile(os.path.join(ifl_directory, file_path)):
            return os.path.join(ifl_directory, file_path)
        else:
            return None