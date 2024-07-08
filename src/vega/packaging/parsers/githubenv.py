"""Module for holding the parser for the github env file"""
import re

from vega.packaging import commits, decorators
from vega.packaging.parsers import abstract_parser


class GitEnv(abstract_parser.AbstractFileParser):
    """Parser for the git env file."""
    FILENAME_REGEX = re.compile("set_env_[a-z0-9-]+", re.I)
    TEMPLATE = ""
    AUTOCREATE = False
    PRIORITY = 5

    @property
    def version(self) -> str:
        """The semantic version parsed from this changelog.md file."""
        if not self._version:
            self._version = self.content.get("SEMANTIC_VERSION", None)
        return self._version

    def create(self):
        """Creates a GitHub env file if it doesn't exist with some default values."""
        with open(self.path, "w") as handle:
            handle.write(self.TEMPLATE)

    def read(self) -> dict:
        """Reads the content of the GitHub env file"""
        content = {}
        with open(self.path, "r") as handle:
            # This code makes the assumption that the first = is the separator for the key value pair of the
            # GitHub envs
            for line in handle.readlines():
                line = line.strip()
                if line:
                    key, value = line.split("=", 1)
                    content[key] = value
        return content

    @decorators.autocreate
    def update(self, commit_message: commits.CommitMessage):
        """Updates the content of the changelog.md file with data from the commit message.

        Args:
            commit_message: The message to update the changelog with.
        """
        self.update_version(commit_message)

        # Add semantic version environment variable to the GitHub env
        self.content["SEMANTIC_VERSION"] = commit_message.semantic_version

        # Update the file
        with open(self.path, "w") as handle:
            handle.writelines([f"{key}={value}" for key, value in self.content.items()])
