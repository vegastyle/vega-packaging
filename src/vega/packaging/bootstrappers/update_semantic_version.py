"""Python script for parsing commit messages and updating files related to packaging.

This supports any file that has had a parser made for it.
"""
import os
import argparse

from vega.packaging import commits
from vega.packaging import factory
from vega.packaging import io
from vega.packaging import log

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
    parser.add_argument("-c", "--changelog_path", help="path to the changelog markdown file to update")
    parser.add_argument("-p", "--pyproject_path", help="path to the pyproject to update")
    parser.add_argument("-r", "--react_package_path", help="path to the react package.json file to update")
    parser.add_argument("--cargo_path", help="path to the Cargo.toml file to update")
    parser.add_argument("-g", "--github_env", help="set the semantic revision env variable on git",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-v", "--verbose", help="print out debug statements",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-l", "--log_to_disk", help="saves out logs to disk",
                        action=argparse.BooleanOptionalAction)
    return parser.parse_args()



def update_semantic_version(message_str: str, paths: list[str], match=True):
    """Updates the semantic version of the provided file paths ,if they are supported, based on the contents of the message string.

    Args:
        message_str: string to be parsed to determine how to update the semantic version
        paths: list of files whose files should be updated.
    """
 
    # Parse commit message
    commit_message = commits.CommitMessage(message_str)
    if not commit_message.is_valid: 
        return False
    
    # Get file parsers
    packaging_files = []

    for path in paths:
        packaging_file = factory.get_parser_from_path(path)
        if not packaging_file or (not packaging_file.exists and not packaging_file.AUTOCREATE):
            continue
        packaging_files.append(packaging_file)

    # Update files based on parsing priority
    packaging_files.sort(key=lambda value: value.PRIORITY)
    semantic_version = None
    if match:
        semantic_version = packaging_files[0].version.start_value()

    for packaging_file in packaging_files:
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
    explicit_paths = [args.pyproject_path, args.changelog_path, args.react_package_path, args.cargo_path]
    if args.github_env:
        explicit_paths.append(os.environ.get("GITHUB_ENV", None))

    ignored = True
    for message in [args.subject, args.description]:
        logger.debug(f"Parsing commit message: {message}")
        # Update semantic version
        filepath_generator = io.yield_paths(args.directory, explicit_paths)
        message_parsed = update_semantic_version(message, filepath_generator)
        if message_parsed:
            ignored = False
            break

    if ignored:
        message = "\n\n".join([args.subject, args.description])
        logger.warning(f"Ignoring Commit:\n\t{message}")
    elif args.github_env:
        github_env_path = os.environ.get("GITHUB_ENV", "")
        if github_env_path:
            seen_build_types = set()
            for path in io.yield_paths(args.directory, explicit_paths):
                pf = factory.get_parser_from_path(path)
                if pf and pf.IS_BUILD_FILE and pf.BUILD_TYPE is not None:
                    seen_build_types.add(pf.BUILD_TYPE)
            with open(github_env_path, "a") as gh_env:
                for build_type in seen_build_types:
                    env_key = f"BUILD_{build_type.name}"
                    gh_env.write(f"{env_key}=True\n")
                    logger.info(f"Wrote {env_key}=True to GITHUB_ENV")


if __name__ == "__main__":
    main()
