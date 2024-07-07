"""Module for holding the parser for the changelog.md file"""
import re

from vega.packaging import commits, decorators
from vega.packaging.parsers import abstract_parser


class Changelog(abstract_parser.AbstractFileParser):
    """Parser for the changelog.md file."""
    FILENAME_REGEX = re.compile("CHANGELOG.md", re.I)
    TEMPLATE = """# Changelog
    
All notable changes to the project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

"""
    PRIORITY = 2

    def __init__(self, path: str):
        """Constructor

        Args:
            path: path to the changelog.md file
        """
        super(Changelog, self).__init__(path)
        self._new_content_index = None

    @property
    def version(self) -> str:
        """The semantic version parsed from this changelog.md file."""
        if not self._version:
            for index, line in enumerate(self.content):
                # At the first match of a semantic version stop and store it for later
                if re.match("## \[[0-9]", line):
                    self._version = re.search("[0-9]+.[0-9]+.[0-9]+", line).group()
                    self._new_content_index = index
                    break
        return self._version

    def create(self):
        """Creates a changelog file if it doesn't exist with some default values."""
        with open(self.path, "w+") as handle:
            handle.write(self.TEMPLATE)

    def read(self) -> list:
        """Reads the changelog.md file."""
        with open(self.path, "r+") as handle:
            return list(handle.readlines())

    @decorators.autocreate
    def update(self, commit_message: commits.CommitMessage):
        """Updates the content of the changelog.md file with data from the commit message.

        Args:
            commit_message: The message to update the changelog with.
        """
        self.update_version(commit_message)

        # Add new changelog
        if self._new_content_index is not None:
            self.content.insert(self._new_content_index, commit_message.markdown)
        else:
            self.content.extend(["\n", commit_message.markdown])

        # Update the file
        with open(self.path, "w+") as handle:
            handle.writelines(self.content)
