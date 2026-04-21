"""Module for holding the parser for the changelog.md file"""
import re
import os

from vega.packaging import commits, decorators, versions
from vega.packaging.parsers import abstract_parser


class Changelog(abstract_parser.AbstractFileParser):
    """Parser for the changelog.md file."""
    AUTOCREATE = True
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
    def package(self) -> str: 
        """ The name of the package that this file defines if it is file that defines a package build"""
        if not self._package:
            self._package = os.path.basename(os.path.dirname(self.path))
        return self._package
    
    @property
    def insert_version_index(self) -> int:
        """The index to insert the new version markdown info"""
        if self._insert_version_index is None:
            self.__get_insert_version_index()
        return self._insert_version_index

    def __get_insert_version_index(self):
        """Gets the version and index where to insert the new version markdown changelog."""
        for index, line in enumerate(self.content or []):
            regex = self.VERSION_REGEX.match(line)
            # At the first match of a semantic version stop and store it for later
            if regex:
                # We do this to make sure we don't override the current version if it exists
                self._version = self._version or versions.SemanticVersion(regex.group("version"))
                self._insert_version_index = index
                break

        if not self._version: 
            self._version = versions.SemanticVersion(self.DEFAULT_VERSION)

    def create(self):
        """Creates a changelog file if it doesn't exist with some default values."""
        with open(self.path, "w") as handle:
            handle.write(self.TEMPLATE)

    def read(self) -> list:
        """Reads the changelog.md file."""
        with open(self.path, "r") as handle:
            return list(handle.readlines())

    @decorators.autocreate
    def update(self, commit_message: commits.CommitMessage, semantic_version: versions.SemanticVersion|str):
        """Updates the content of the changelog.md file with data from the commit message.

        Args:
            commit_message: The message to update the changelog with.
        """
        super(Changelog, self).update(commit_message, semantic_version)

        # Add new changelog
        if self.insert_version_index is not None:
            self.content.insert(self.insert_version_index, commit_message.markdown(self.version))
        else:
            self.content.extend(["\n", commit_message.markdown(self.version)])

        # Update the file
        with open(self.path, "w") as handle:
            handle.writelines(self.content)

    def changes(self, version=None, since=None) -> str:
        """Returns changelog content for a version range.

        Args:
            version: target version (e.g. "1.0.0"). If None, uses the latest version.
            since: exclusive lower bound version (e.g. "0.1.0"). If None, only the single
                   section identified by `version` is returned.
        """
        lines = self.content or []
        start_idx = None
        end_idx = len(lines)

        target = str(version) if version else None
        lower = str(since) if since else None

        for i, line in enumerate(lines):
            match = self.VERSION_REGEX.match(line)
            if not match:
                continue
            v = match.group("version")

            if start_idx is None:
                if target is None or v == target:
                    start_idx = i
            else:
                if lower is None or v == lower:
                    end_idx = i
                    break

        if start_idx is None:
            return ""
        return "".join(lines[start_idx:end_idx])
