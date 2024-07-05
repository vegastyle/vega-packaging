"""Python script for parsing commit messages and updating files related to packaging.

This supports any file that has had a parser made for it.
"""
import os

import argparse

from vega.packaging import commits
from vega.packaging import factory


def parse_args():
    """Parses the arguments passed to this module"""
    parser = argparse.ArgumentParser(
        prog='Update Semantic Version',
        description='Updates the semantic version of the given files based on a commit message',
    )
    parser.add_argument("-m", "--message", help="message to parse for the changelog", required=True)
    parser.add_argument("-c", "--changelog_path", help="path to the changelog markdown file to update")
    parser.add_argument("-p", "--pyproject_path", help="path to the pyproject to update")
    parser.add_argument("-sg", "--set_git_env", help="sets the final revision value as a variable on git",
                        action=argparse.BooleanOptionalAction)

    return parser.parse_args()

#C:\Users\Owner\Desktop\Projects\vega-packaging\src\vega\packaging\bootstrappers\update_semantic_version.py --changelog CHANGELOG.md --pyproject pyproject.toml --message #major #fixed big update
def main():
    """Main function to call in this bootstrapper"""
    args = parse_args()

    if "#" in args.message and "#ignore" not in args.message.lower():
        message = commits.CommitMessage(args.message)
        for path in (args.pyproject_path, args.changelog_path):
            packaging_file = factory.get_parser(path)
            if not packaging_file:
                continue

            elif not packaging_file.exists and not packaging_file.AUTOCREATE:
                continue

            packaging_file.update(message)

        if args.set_git_env and 'GITHUB_ENV' in os.environ:
            # TODO: Move to its own module
            env_file = os.getenv('GITHUB_ENV')
            with open(env_file, "a") as myfile:
                myfile.write(f"SEMANTIC_VERSION={message.semantic_version}")

        print(f"Updated package with revision number {message.semantic_version}")
    else:
        print(f"Ignoring Commit:\n\t{args.message}")


if __name__ == "__main__":
    main()
