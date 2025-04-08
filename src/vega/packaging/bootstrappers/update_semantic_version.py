"""Python script for parsing commit messages and updating files related to packaging.

This supports any file that has had a parser made for it.
"""
import os
import datetime
import argparse
import platform
import logging

from vega.packaging import commits
from vega.packaging import factory

logger = logging.getLogger(__name__)


def parse_args():
    """Parses the arguments passed to this module"""
    parser = argparse.ArgumentParser(
        prog='Update Semantic Version',
        description='Updates the semantic version of the given files based on a commit message',
    )
    parser.add_argument("-m", "--message", help="message to parse for the changelog", required=True)
    parser.add_argument("-d", "--directory", help="directory to look for files to update", default=os.getcwd())
    parser.add_argument("-c", "--changelog_path", help="path to the changelog markdown file to update")
    parser.add_argument("-p", "--pyproject_path", help="path to the pyproject to update")
    parser.add_argument("-r", "--react_package_path", help="path to the react package.json file to update")
    parser.add_argument("-g", "--github_env", help="set the semantic revision env variable on git",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-v", "--verbose", help="print out debug statements",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-l", "--log_to_disk", help="saves out logs to disk",
                        action=argparse.BooleanOptionalAction)
    return parser.parse_args()


def setup_logging(verbose: bool = False, write_to_disk: bool = True):
    """Sets up logging for this application.

    Args:
        verbose: write debug and info statements to stdout. Defaults to False.
        write_to_disk: write logs to disk. Defaults to True.
    """
    default_log_directory = os.path.join(os.getcwd(), "logs")
    current_time = datetime.datetime.now(datetime.UTC).strftime("%Y_%m_%dT%H_%M_%SZ")
    log_path = os.path.join(default_log_directory, f"update_semantic_version_{current_time}.log")
    if not os.path.exists(default_log_directory):
        os.makedirs(default_log_directory)

    log_format = "%(asctime)s %(message)s"
    log_date_format = "%m/%d/%Y %I:%M:%S %p"
    logging_level = logging.DEBUG if verbose else logging.WARNING
    handlers = [logging.StreamHandler()]
    if write_to_disk:
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    logging.basicConfig(format=log_format,
                        datefmt=log_date_format,
                        handlers=handlers,
                        level=logging_level)


def yield_paths(args: argparse.ArgumentParser):
    """Yields the paths should be parsed by this cli command based on the contents of the args parser.

    Args:
        args: the parsed command line arguments

    Yields:
        str
    """
    # yield of files that are direct children of the given directory
    paths = []
    logger.debug(f"Scanning {args.directory} for files to update.")
    for filename in os.listdir(args.directory):
        if os.path.isfile(filename):
            path = os.path.join(args.directory, filename)
            yield path
            paths.append(path)

    # Add explicitly set paths in args
    explicit_paths = [args.pyproject_path, args.changelog_path, args.react_package_path]
    if args.github_env:
        explicit_paths.append(os.environ.get("GITHUB_ENV", None))

    is_windows = platform.system() == "Windows"
    for path in explicit_paths:
        if not path:
            # Skip none values
            continue
        elif (is_windows and not os.path.splitdrive(path)[0]) or (not is_windows and not path.startswith("/")):
            # If no root path is specified on the explicitly set files
            # we assume that they are relative to the given directory
            path = os.path.join(args.directory, path)
        if path not in paths:
            yield path


def update_semantic_version(message_str: str, paths: list[str]):
    """Updates the semantic version of the provided file paths ,if they are supported, based on the contents of the message string.

    Args:
        message_str: string to be parsed to determine how to update the semantic version
        paths: list of files whose files should be updated.
    """
    if "#" in message_str and "#ignore" not in message_str.lower():
        # Parse commit message
        message = commits.CommitMessage(message_str)

        # Get file parsers
        packaging_files = []

        for path in paths:
            packaging_file = factory.get_parser_from_path(path)
            if not packaging_file or (not packaging_file.exists and not packaging_file.AUTOCREATE):
                continue
            packaging_files.append(packaging_file)

        # Update files based on parsing priority
        packaging_files.sort(key=lambda value: value.PRIORITY)
        for packaging_file in packaging_files:
            packaging_file.update(message)
            logger.info(f"Updated {packaging_file.path} with revision number {message.semantic_version}")
    else:
        logger.warning(f"Ignoring Commit:\n\t{message_str}")


def main():
    """Main function to call in this bootstrapper"""
    # Parse args
    args = parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose, write_to_disk=args.log_to_disk)

    # Update semantic version
    update_semantic_version(args.message, yield_paths(args))


if __name__ == "__main__":
    main()
