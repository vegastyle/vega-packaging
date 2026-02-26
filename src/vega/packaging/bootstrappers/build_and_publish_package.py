"""Python script for parsing commit messages and updating files related to packaging.

This supports any file that has had a parser made for it.
"""
import os
import argparse

from vega.packaging import commits
from vega.packaging import const
from vega.packaging import factory
from vega.packaging import io
from vega.packaging import log

logger = log.get(__name__)


def parse_args():
    """Parses the arguments passed to this module"""
    parser = argparse.ArgumentParser(
        prog='Build and Publish',
        description='Builds and publishes the packages to their respective repositories',
    )
    parser.add_argument("-s", "--subject", help="subject of the commit message", required=True)
    parser.add_argument("-m", "--description", help="description of the commit message")
    parser.add_argument("-d", "--directory", help="directory to look for files to update", default=os.getcwd())
    parser.add_argument("-p", "--pypi_registry", help="registry to publish python package to")
    parser.add_argument("-n", "--npm_registry", help="registry to publish npm packages to")
    parser.add_argument("-r", "--docker_registry", help="registry to publish docker images to")
    parser.add_argument("-v", "--verbose", help="print out debug statements",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-l", "--log_to_disk", help="saves out logs to disk",
                        action=argparse.BooleanOptionalAction)
    return parser.parse_args()



def build_and_publish(message_str: str, paths: list[str], repositories=None):
    """Updates the semantic version of the provided file paths ,if they are supported, based on the contents of the message string.

    Args:
        message_str: string to be parsed to determine how to update the semantic version
        paths: list of files whose files should be updated.
    """
 
    # Parse commit message
    message = commits.CommitMessage(message_str, auto_parse=False)
    if not message.is_valid: 
        return False
    
    # repositories
    repositories = repositories or {}

    # Get file parsers
    packaging_files = []

    for path in paths:
        packaging_file = factory.get_parser_from_path(path)
        if packaging_file and packaging_file.IS_BUILD_FILE and packaging_file.BUILD_TYPE in repositories:
            packaging_files.append(packaging_file)

    # Update files based on parsing priority
    packaging_files.sort(key=lambda value: value.PRIORITY)
    for packaging_file in packaging_files:
        logger.info(f"Building {packaging_file.path}")
        packaging_file.registry = repositories[packaging_file.BUILD_TYPE]
        packaging_file.build(message)
        logger.info(f"Publishing to {repositories[packaging_file.BUILD_TYPE]}")
        packaging_file.publish(repositories[packaging_file.BUILD_TYPE])
    return True


def main():
    """Main function to call in this bootstrapper"""
    # Parse args
    args = parse_args()

    # Setup logging
    log.setup("build_and_publish", verbose=args.verbose, write_to_disk=args.log_to_disk)

    # Build repositories dict from args
    repositories = {}
    if args.pypi_registry:
        repositories[const.BuildTypes.PYTHON] = args.pypi_registry
    if args.npm_registry:
        repositories[const.BuildTypes.NPM] = args.npm_registry
    if args.docker_registry:
        repositories[const.BuildTypes.DOCKER] = args.docker_registry

    ignored = True
    for message in [args.subject, args.description]:
        if not message:
            continue
        logger.debug(f"Parsing commit message: {message}")
        # Build and publish packages
        filepath_generator = io.yield_paths(args.directory, [])
        message_parsed = build_and_publish(message, filepath_generator, repositories)
        if message_parsed:
            ignored = False
            break

    if ignored:
        logger.warning(f"Ignoring Commit:\n\t{args.subject}")


if __name__ == "__main__":
    main()
