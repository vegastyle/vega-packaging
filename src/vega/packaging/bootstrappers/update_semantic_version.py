"""Python script for parsing commit messages and updating files related to packaging.

This supports any file that has had a parser made for it.
"""
import os
import argparse

from vega.packaging import commits
from vega.packaging import factory
from vega.packaging import io
from vega.packaging import log
from vega.packaging import const

logger = log.get(__name__)


def parse_args():
    """Parses the arguments passed to this module"""
    parser = argparse.ArgumentParser(
        prog='Update Semantic Version',
        description='Updates the semantic version of the given files based on a commit message',
    )
    parser.add_argument("-s", "--subject", help="subject of the message to parse for the changelog", required=True)
    parser.add_argument("-m", "--description", help="description of the message to parse for the changelog")
    parser.add_argument("-d", "--directory", help="directory to look for files to update", default=os.getcwd())
    parser.add_argument("-cp", "--changelog_path", help="path to the changelog markdown file to update")
    parser.add_argument("-pp", "--pyproject_path", help="path to the pyproject to update")
    parser.add_argument("-rp", "--react_package_path", help="path to the react package.json file to update")
    parser.add_argument("-dp", "--dockerfile_path", help="path to the dockerfile file to track")
    parser.add_argument("-dr", "--docker_registry", help="registry path in repo/name format to query for information")
    parser.add_argument("-ca", "--cargo_path", help="path to the Cargo.toml file to update")
    parser.add_argument("-gh", "--github_env", help="set the semantic revision env variable on git",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-v", "--verbose", help="print out debug statements",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-l", "--log_to_disk", help="saves out logs to disk",
                        action=argparse.BooleanOptionalAction)
    return parser.parse_args()


def get_parsers_dict(paths: list[str]) -> dict:
    parsers_dict = {"builds":{},
                    "ordered": []}
    
    for path in paths:
        file_parser = factory.get_parser_from_path(path)
        if not file_parser or (not file_parser.exists and not file_parser.AUTOCREATE):
            continue
        parsers_dict["ordered"].append(file_parser)
        if file_parser.BUILD_TYPE is not None:
            parsers_dict["builds"].setdefault(file_parser.BUILD_TYPE, []).append(file_parser)

    # Sort by Priority
    parsers_dict["ordered"].sort(key=lambda file_parser: file_parser.PRIORITY)

    return parsers_dict

def update_semantic_version(message_str: str, paths: list[str] | None = None, match=True, parsers: dict=None):
    """Updates the semantic version of the provided file paths, if they are supported, based on the contents of the message string.

    Args:
        message_str: string to be parsed to determine how to update the semantic version
        paths: list of files whose files should be updated.
    """
    # Parse commit message
    commit_message = commits.CommitMessage(message_str)
    if not commit_message.is_valid:
        return False

    if not parsers:
        parsers = get_parsers_dict(paths or [])

    if not parsers["ordered"]:
        return False

    semantic_version = None
    if match:
        version_value = parsers["ordered"][0].version
        semantic_version = version_value.start_value() if hasattr(version_value, "start_value") else version_value

    for packaging_file in parsers["ordered"]:
        packaging_file.update(commit_message, semantic_version)
        logger.info(f"Updated {packaging_file.path} with revision number {packaging_file.version}")
    return True


def main():
    """Main function to call in this bootstrapper"""
    # Parse args
    args = parse_args()

    # Setup logging
    log.setup("update_semantic_version", verbose=args.verbose, write_to_disk=args.log_to_disk)

    # Add explicitly set paths in args
    explicit_paths = [args.pyproject_path, args.changelog_path, args.react_package_path, args.cargo_path, args.dockerfile_path]
    if args.github_env:
        explicit_paths.append(os.environ.get("GITHUB_ENV", None))

    parsers_dict = get_parsers_dict(io.yield_paths(args.directory, explicit_paths))
    
    # Docker files are special in the sense that we need to track the tag on the repository to figure out 
    # the version of the latest image. It isn't stored in the dockerfile itself. 
    if args.docker_registry and const.BuildTypes.DOCKER in parsers_dict["builds"]:
        for docker_parser in parsers_dict["builds"][const.BuildTypes.DOCKER]:
            docker_parser.registry = args.docker_registry

    # Set the the build files that were found to the github env parser
    if args.github_env:
        build_types = [each.value for each in parsers_dict["builds"].keys()]
        for file_parser in reversed(parsers_dict["ordered"]):
            if file_parser.NAME == "GitEnv":
                file_parser.builds = build_types
                break

    ignored = True
    for message in filter(None, [args.subject, args.description]):
        logger.debug(f"Parsing commit message: {message}")
        message_parsed = update_semantic_version(message, parsers=parsers_dict)
        if message_parsed:
            ignored = False

    if ignored:
        message = "\n\n".join([args.subject, args.description])
        logger.warning(f"Ignoring Commit:\n\t{message}")


if __name__ == "__main__":
    main()
