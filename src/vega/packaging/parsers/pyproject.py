"""Module for holding the code for parsing the pyproject.toml files"""
import os
import re
import subprocess

import toml

from vega.packaging import commits, decorators, const, versions
from vega.packaging import contextmanagers
from vega.packaging.parsers import abstract_parser


class PyProject(abstract_parser.AbstractFileParser):
    """Parser for pyproject.toml files"""
    NAME = "PyProject"
    FILENAME_REGEX = re.compile("pyproject.toml", re.I)
    TEMPLATE = {"build-system":
                    {"requires": ["setuptools >= 61.0"],
                     "build-backend": "setuptools.build_meta"},
                "project": {
                    "name": None}}
    DEFAULT_REGISTRY = "https://upload.pypi.org/legacy/"
    PRIORITY = 1
    IS_BUILD_FILE = True
    BUILD_TYPE = const.BuildTypes.PYTHON

    @property
    def version(self) -> str:
        """The semantic version parsed from this file."""
        if not self._version:
            self._version = versions.SemanticVersion(self.content.get("project", {}).get("version", self.DEFAULT_VERSION))
        return self._version

    @property
    def content(self) -> dict:
        """The contents of this pyproject.toml file"""
        return super(PyProject, self).content or {}

    @property
    def package(self) -> str: 
        """ The name of the package that this file defines if it is file that defines a package build"""
        if not self._package:
            self._package = self.read()["project"]["name"] 
        return self._package
    
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
    def update(self, commit_message: commits.CommitMessage, semantic_version: versions.SemanticVersion|str):
        """Updates the contents of the pyproject.toml file with data from the commit message.

        Args:
            commit_message: the message to use for updating this file.
        """
        super(PyProject, self).update(commit_message, semantic_version)

        # Update pyproject.toml version
        self.content["project"]["version"] = str(self.version)

        # Update the file
        with open(self.path, "w") as handle:
            toml.dump(self.content, handle)

    def build(self, commit_message=None):
        """Builds the Python package."""
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            result = subprocess.run(
                ["uv", "run", "--with", "build", "--with", "setuptools>=61.0", "python", "-m", "build", "--no-isolation"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Build failed: {result.stderr}")
            # Find the built wheel in dist/
            dist_dir = "dist"
            for filename in os.listdir(dist_dir):
                if filename.endswith(".whl"):
                    self._build = os.path.join(dist_dir, filename)
                    break

    def publish(self, registry=None):
        """Publishes the Python package using twine."""
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            registry = registry or self._registry
            if not self._build:
                raise RuntimeError("Must build before publishing")
            cmd = ["uv", "run", "--with", "twine", "python", "-m", "twine", "upload"]
            if registry:
                cmd.extend(["--repository-url", registry])
            cmd.append(self._build)
            result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
            if result.returncode != 0:
                error_parts = []
                for part in (result.stderr, result.stdout):
                    if isinstance(part, str) and part.strip():
                        error_parts.append(part.strip())
                error_output = "\n".join(error_parts) if error_parts else "unknown error"
                raise RuntimeError(f"Publish failed: {error_output}")
