"""Module for holding the parser for the github env file"""
import re

from vega.packaging import commits, decorators, versions
from vega.packaging.parsers import abstract_parser


class GitEnv(abstract_parser.AbstractFileParser):
    """Parser for the git env file."""
    NAME = "GitEnv"
    FILENAME_REGEX = re.compile("set_env_[a-z0-9-]+", re.I)
    TEMPLATE = ""
    PRIORITY = 4

    @property
    def version(self) -> str:
        """The semantic version parsed from this changelog.md file."""
        if not self._version:
            self._version = versions.SemanticVersion(self.content.get("SEMANTIC_VERSION", self.DEFAULT_VERSION))
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
    def update(self, commit_message: commits.CommitMessage, semantic_version: versions.SemanticVersion|str):
        """Updates the content of the changelog.md file with data from the commit message.

        Args:
            commit_message: The message to update the changelog with.
        """
        super(GitEnv, self).update(commit_message, semantic_version)

        # Add semantic version environment variable to the GitHub env
        self.content["SEMANTIC_VERSION"] = str(self.version)
        self.content["PUBLISH"] = str(commit_message.publish)
        self.content["RELEASE"] = str(commit_message.release)

        # Update the file
        with open(self.path, "w") as handle:
            handle.writelines([f"\n{key}={value}" for key, value in self.content.items()])
