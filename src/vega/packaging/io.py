import os
import platform
import logging 

logger = logging.getLogger(__name__)


def yield_paths(directory=None, additional_paths=None):
    """Yields the paths should be parsed by this cli command based on the contents of the args parser.

    Args:
        directory (str): path to directory to scan for files.
        additional_paths: additional files that should be returned even if they don't exist. 
                        This is intended to be used for ensuring files are present even when mising on disk. 

    Yields:
        str
    """
    # yield of files that are direct children of the given directory
    paths = []
    additional_paths = additional_paths or []
    logger.debug(f"Scanning {directory} for files")
    for filename in os.listdir(directory):
        if os.path.isfile(filename):
            path = os.path.join(directory, filename)
            yield path
            paths.append(path)

    is_windows = platform.system() == "Windows"
    for path in additional_paths:
        if not path:
            # Skip none values
            continue
        elif (is_windows and not os.path.splitdrive(path)[0]) or (not is_windows and not path.startswith("/")):
            # If no root path is specified on the explicitly set files
            # we assume that they are relative to the given directory
            path = os.path.join(directory, path)
        if path not in paths:
            yield path