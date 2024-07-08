"""Module for holding the code for parsing the pyproject.toml files"""
import os
import re

import toml

from vega.packaging import commits, decorators
from vega.packaging.parsers import abstract_parser


class PyProject(abstract_parser.AbstractFileParser):
    """Parser for pyproject.toml files"""
    FILENAME_REGEX = re.compile("pyproject.toml", re.I)
    TEMPLATE = {"build-system":
                    {"requires": ["setuptools >= 61.0"],
                     "build-backend": "setuptools.build_meta"},
                "project": {
                    "name": None}}
    AUTOCREATE = False
    PRIORITY = 1

    @property
    def version(self) -> str:
        """The semantic version parsed from this file."""
        if not self._version:
            self._version = self.content.get("project", {}).get("version", None)
        return self._version

    @property
    def content(self) -> dict:
        """The contents of this pyproject.toml file"""
        return super(PyProject, self).content or {}

    def create(self):
        """Creates a pyproject.toml file with some default values."""
        content = dict(self.TEMPLATE)
        content["project"]["name"] = os.path.split(os.path.dirname(self.path))[-1]
        content["project"]["version"] = self.DEFAULT_VERSION

        with open(self.path, "w") as handle:
            toml.dump(content, handle)

    def read(self) -> dict:
        """Reads the contents of the pyproject.toml file"""
        return toml.load(self.path)

    @decorators.autocreate
    def update(self, commit_message: commits.CommitMessage):
        """Updates the contents of the pyproject.toml file with data from the commit message.

        Args:
            commit_message: the message to use for updating this file.
        """
        self.update_version(commit_message)

        # Update pyproject.toml version
        self.content["project"]["version"] = self.version

        # Update the file
        with open(self.path, "w") as handle:
            toml.dump(self.content, handle)
