"""Module for holding the code for parsing the pyproject.toml files"""
import os

import toml

from vega.packaging import commits
from vega.packaging.parsers import abstract_parser


class PyProject(abstract_parser.AbstractFileParser):
    """Parser for pyproject.toml files"""
    FILENAME = "pyproject.toml"
    TEMPLATE = {"build-system":
                    {"requires": ["setuptools >= 61.0"],
                     "build-backend": "setuptools.build_meta"},
                "project": {
                    "name": None}}
    AUTOCREATE = False

    @property
    def version(self) -> str:
        """The semantic version parsed from this file."""
        if not self._version:
            self._version = self.content.get("project", {}).get("version", None)
        return self._version

    @property
    def content(self) -> dict:
        """The contents of this pyproject.toml file"""
        if not self._content and self.exists:
            self._content = toml.load(self._path)
        return self._content or {}

    def create(self):
        """Creates a pyproject.toml file with some default values."""
        content = dict(self.TEMPLATE)
        content["project"]["name"] = os.path.split(os.path.dirname(self._path))[-1]
        content["project"]["version"] = self.DEFAULT_VERSION

        with open(self._path, "w+") as handle:
            toml.dumps(content, handle)

    def update(self, commit_message: commits.CommitMessage):
        """Updates the contents of the pyproject.toml file with data from the commit message.

        Args:
            commit_message: the message to use for updating this file.
        """

        # TODO: Create a decorator for this autocreate logic
        if not self.exists and self.AUTOCREATE:
            self.create()
        else:
            raise FileNotFoundError(f"{self._path} does not exist")

        self.update_version(commit_message)

        # Update pyproject.toml version
        self.content["project"]["version"] = self.version

        # Update the file
        with open(self._path, "w+") as handle:
            toml.dumps(self.content, handle)
