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
    VERSION_REGEX = re.compile("## \\[(?P<version>[0-9]+.[0-9]+.[0-9]+)\\]")

    def __init__(self, path: str):
        """Constructor

        Args:
            path: path to the changelog.md file
        """
        super(Changelog, self).__init__(path)
        self._insert_version_index = None

    @property
    def version(self) -> str:
        """The semantic version parsed from this changelog.md file."""
        if not self._version:
            self.__get_insert_version_index()
        return self._version

    @property
    def insert_version_index(self) -> int:
        """The index to insert the new version markdown info"""
        if not self._insert_version_index:
            self.__get_insert_version_index()
        return self._insert_version_index

    def __get_insert_version_index(self):
        """Gets the version and index where to insert the new version markdown changelog."""
        for index, line in enumerate(self.content):
            regex = self.VERSION_REGEX.match(line)
            # At the first match of a semantic version stop and store it for later
            if regex:
                # We do this to make sure we don't override the
                self._version = self._version or regex.group("version")
                self._insert_version_index = index
                break

    def create(self):
        """Creates a changelog file if it doesn't exist with some default values."""
        with open(self.path, "w") as handle:
            handle.write(self.TEMPLATE)

    def read(self) -> list:
        """Reads the changelog.md file."""
        with open(self.path, "r") as handle:
            return list(handle.readlines())

    @decorators.autocreate
    def update(self, commit_message: commits.CommitMessage):
        """Updates the content of the changelog.md file with data from the commit message.

        Args:
            commit_message: The message to update the changelog with.
        """
        self.update_version(commit_message)

        # Add new changelog
        if self.insert_version_index is not None:
            self.content.insert(self.insert_version_index, commit_message.markdown)
        else:
            self.content.extend(["\n", commit_message.markdown])

        # Update the file
        with open(self.path, "w") as handle:
            handle.writelines(self.content)
