import os
import re
import sys

import maya.cmds

RE_DRIVE_LETTER = re.compile(r"^[a-zA-Z]:[\\/]")
RE_PATH_TOKEN = re.compile(r'<(?P<token>[^>]+)>')
MAYA_FRAME_NUMBER_TOKEN = 'f'
# Tuples of node types and the corresponding attribute containing texture path patterns
NODE_TYPES_ATTRS = (
    ('file', 'computedFileTextureNamePattern'),
    ('aiImage', 'filename'),
    ('imagePlane', 'imageName')
)

# A sequence of tuples mapping arnold texture path token names to regex patterns that they should match
# These were formed by consulting https://docs.arnoldrenderer.com/display/A5AFMUG/Tokens
ARNOLD_TOKEN_REGEXES = (
    (
        re.compile("^f$"),
        r"(?P<frame>\d+)"
    ),
    (
        re.compile("^tile$"),
        r"_u[1-9]_v[1-9]"
    ),
    (
        re.compile("^udim$" ),
       r"(?:"
       r"100[1-9]"
       r"|10[1-9]\d"
       r"|1[1-9]\d{2}"
       r"|[2-9]\d{3}"
       r")"
    )
)


class TokenInDirectoryError(RuntimeError):
    """Exception indicating a token was found in the directory portion of a path"""
    pass


def _arnold_pattern_to_regex(pattern):
    """
    Converts an Arnold texture path into a regular expression. All tokens except the frame number are converted to a
    generic r".*" regex fragment. The special frame number token "<f>" is converted to a named capture group
    "(?P<frame>\d+)".

    :param pattern: An Arnold texture path that may contain a number of path tokens
    :return: A regular expression that can be used to match textures paths
    """
    regex = '^'
    last_index = 0

    for match in RE_PATH_TOKEN.finditer(pattern):
        regex += re.escape(pattern[last_index:match.start(0)])
        token = match.group('token')
        for token_re, path_re in ARNOLD_TOKEN_REGEXES:
            if token_re.search(token):
                regex += path_re
                break
        else:
            # We cannot anticipate what new tokens will be introduced and break this parsing but the tokens should
            # not transcend a path separator
            regex += r'[^\\/]+'
        last_index = match.end(0)

    regex += re.escape(pattern[last_index:])
    regex += '$'

    # We look for drive-letter paths to get unit tests running on non-Windows platforms working
    flags = re.IGNORECASE if sys.platform.startswith('win') or RE_DRIVE_LETTER.match(pattern) else 0

    return re.compile(regex, flags=flags)


def find_texture_files():
    """
    A generator function that locates all nodes that point to external image files.

    :return: An iterator that yields two element tuples. The first element is the node name, and the second element
             is the image path (including unexpanded filename tokens such as "<f>").
    """

    for node_type, attr_name in NODE_TYPES_ATTRS:
        for node in maya.cmds.ls(type=node_type):
            tokenized_path = maya.cmds.getAttr(node + '.' + attr_name)
            yield node, tokenized_path


def expand_arnold_tokenized_path_to_deadline(pattern):
    """
    Expand an Arnold tokenized texture pattern to Deadline's frame-independent path pattern(s). Arnold understands
    a set of tokens (see https://docs.arnoldrenderer.com/display/AFMUG/Tokens) in texture paths. This function
    scans the filesystem for matching textures and map-reduces them to a minimal set of path patterns for use by
    Deadline. These paths are reduced using the hash (#) character for frame numbers.

    This function raises a TokenInDirectoryError if there are no tokens in the directory portion of the path. This is a
    limitation of the scope of implementation of this function and not an underlying limitation of Maya or Arnold.

    Example: Given a tx_path of "/path/to/foo.<udim>.<f>.exr" and assuming the following files exist:

    /path/to/foo.1001.1.exr
    /path/to/foo.1002.1.exr
    /path/to/foo.1011.1.exr
    /path/to/foo.1012.1.exr
    /path/to/foo.1001.2.exr
    /path/to/foo.1002.2.exr
    /path/to/foo.1011.2.exr
    /path/to/foo.1012.2.exr

    The result will appear as:

    [
        "/path/to/foo.1001.#.exr",
        "/path/to/foo.1002.#.exr",
        "/path/to/foo.1011.#.exr",
        "/path/to/foo.1012.#.exr"
    ]

    :param pattern: A path pattern to the texture (which may contain Arnold texture path tokens)
    :raises TokenInDirectoryError: If the directory contains a path token
    :return: A set of Deadline file patterns that minimally represent the same files represented by the input Arnold
             texture path pattern
    """

    results = set()

    pattern = pattern.replace('\\', '/')
    dirname, basename = os.path.split(pattern)
    # Maya might use forward slashes for paths
    separator = pattern[len(dirname)]

    if dirname and basename and os.path.isdir(dirname):
        # This implementation does not handle tokens in the directory portion of the path. There is no limitation
        # saying we can't extend this function in the future, but the scope has been limited at this point
        if RE_PATH_TOKEN.search(dirname):
            raise TokenInDirectoryError("Tokens are not allowed in the directory portion of the path")

        regex = _arnold_pattern_to_regex(pattern)

        for filename in os.listdir(dirname):
            path = dirname + separator + filename
            match = regex.match(path)
            if match:
                # Replace the frame number with Deadline's frame number token
                try:
                    frame_start, frame_end = match.span('frame')
                except IndexError:
                    # This happens when there is no "frame" capture group
                    pass
                else:
                    # If there is a frame capture group, we replace the digits with placeholders
                    frame_padding_size = frame_end - frame_start
                    frame_padding = '#' * frame_padding_size
                    path = path[:frame_start] + frame_padding + path[frame_end:]
                results.add(path)

    return results


def find_derivative_tx_files():
    """"
    A function that returns all of the derivative TX path patterns (with frame placeholder tokens) that are referenced
    by the scene. This scans all image nodes via `deadlinemaya.textures.find_texture_files`. If the node references a
    path without a ".tx" extension, the path tokens are expanded - with the exception of the frame number. The frame
    number token is replaced with a Deadline frame number (consecutive hash characters). Finally, the extensions are
    swapped with ".tx" and the final result is returned.

    :return: A list of all derivative TX file patterns using Deadline's frame number convention that Arnold would use
             to render the scene
    """

    results = set()

    for node, tokenized_path in find_texture_files():
        extension = os.path.splitext(tokenized_path)[1]

        # Skip if the node points directly to TX files (not a derivative)
        if extension.lower() != ".tx":
            # Expand all path tokens except for the frame number ("<f>") which gets converted to Deadline's frame
            # token ("#")
            try:
                deadline_tokenized_paths = expand_arnold_tokenized_path_to_deadline(tokenized_path)
            except TokenInDirectoryError as e:
                print("Failed to expand texture path \"%s\": %s" % (tokenized_path, str(e)))
                continue

            # Union the results (no duplicates)
            results = results | deadline_tokenized_paths

    results = [
        os.path.splitext(result)[0] + '.tx'
        for result in results
    ]

    return results