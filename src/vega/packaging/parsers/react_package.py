"""Module for holding the code for parsing the package.json files of a React Project"""
import os
import re
import subprocess

import json

from vega.packaging import commits, decorators, const, versions
from vega.packaging import contextmanagers
from vega.packaging.parsers import abstract_parser


class ReactPackage(abstract_parser.AbstractFileParser):
    """Parser for package.json files for React projects"""
    NAME = ""
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
    DEFAULT_REGISTRY = "https://registry.npmjs.org/"
    PRIORITY = 1
    IS_BUILD_FILE = True
    BUILD_TYPE = const.BuildTypes.NPM

    @property
    def version(self) -> str:
        """The semantic version parsed from this file."""
        if not self._version:
            self._version = versions.SemanticVersion(self.content.get("version", self.DEFAULT_VERSION))
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
    def update(self, commit_message: commits.CommitMessage, semantic_version: versions.SemanticVersion|str):
        """Updates the contents of the package.json file with data from the commit message.

        Args:
            commit_message: the message to use for updating this file.
        """
        super(ReactPackage, self).update(commit_message, semantic_version)

        # Update pyproject.toml version
        self.content["version"] = str(self.version)

        # Update the file
        with open(self.path, "w") as handle:
            json.dump(self.content, handle)

    @property
    def package(self) -> str: 
        """ The name of the package that this file defines if it is file that defines a package build"""
        if not self._package:
            self._package = self.read()["name"] 
        return self._package
    
    def build(self, commit_message=None):
        """Builds the NPM package."""
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Build failed: {result.stderr}")
            self._build = "."

    def publish(self, registry=None):
        """Publishes the NPM package."""
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            registry = registry or self._registry
            cmd = ["npm", "publish"]
            if registry:
                cmd.extend(["--registry", registry])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Publish failed: {result.stderr}")