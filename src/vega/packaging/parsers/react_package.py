"""Module for holding the code for parsing the package.json files of a React Project"""
import os
import re

import json

from vega.packaging import commits, decorators
from vega.packaging.parsers import abstract_parser


class ReactPackage(abstract_parser.AbstractFileParser):
    """Parser for package.json files for React projects"""
    FILENAME_REGEX = re.compile("package.json", re.I)
    TEMPLATE = {
      "name": None,
      "private": True,
      "version": "0.0.0",
      "type": "module",
      "scripts": {
      },
      "dependencies": {
        "react": "^19.0.0",
        "react-dom": "^19.0.0"
      },
      "devDependencies": {}
    }
    AUTOCREATE = False
    PRIORITY = 1

    @property
    def version(self) -> str:
        """The semantic version parsed from this file."""
        if not self._version:
            self._version = self.content.get("version", None)
        return self._version

    @property
    def content(self) -> dict:
        """The contents of this package.json file"""
        return super(ReactPackage, self).content or {}

    def create(self):
        """Creates a package.jso file with some default values."""
        repository_name = os.environ.get("GITHUB_REPOSITORY", os.path.dirname(self.path))
        content = dict(self.TEMPLATE)
        content["name"] = os.path.basename(repository_name)
        content["version"] = self.DEFAULT_VERSION

        with open(self.path, "w") as handle:
            json.dump(content, handle, indent=4)

    def read(self) -> dict:
        """Reads the contents of the package.json file"""
        with open(self.path, "r+", encoding="utf-8") as handle:
            return json.load(handle)

    @decorators.autocreate
    def update(self, commit_message: commits.CommitMessage):
        """Updates the contents of the package.json file with data from the commit message.

        Args:
            commit_message: the message to use for updating this file.
        """
        self.update_version(commit_message)

        # Update pyproject.toml version
        self.content["version"] = self.version

        # Update the file
        with open(self.path, "w") as handle:
            json.dump(self.content, handle)
