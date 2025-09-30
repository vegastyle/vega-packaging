"""Module for holding the code for parsing the docker-compose.yaml files"""
import os
import re

import toml

from vega.packaging import commits, decorators
from vega.packaging.parsers import abstract_parser


class DockerCompose(abstract_parser.AbstractFileParser):
    """Parser for docker-compose.yaml files"""
    FILENAME_REGEX = re.compile("docker-compose.yaml", re.I)
    TEMPLATE = {"version": None,
                "services": {"api": {"container_name": None}}}
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
        """The contents of this docker-compose.yaml file"""
        return super(DockerCompose, self).content or {}

    def create(self):
        """Creates a docker-compose.yaml file with some default values."""
        content = dict(self.TEMPLATE)
        content["services"]["api"]["container_name"] = os.path.split(os.path.dirname(self.path))[-1]
        content["version"] = self.DEFAULT_VERSION

        with open(self.path, "w") as handle:
            toml.dump(content, handle)

    def read(self) -> dict:
        """Reads the contents of the docker-compose.yaml file"""
        return toml.load(self.path)

    @decorators.autocreate
    def update(self, commit_message: commits.CommitMessage):
        """Updates the contents of the docker-compose.yaml file with data from the commit message.

        Args:
            commit_message: the message to use for updating this file.
        """
        self.update_version(commit_message)

        # Update docker-compose.yaml version
        self.content["version"] = self.version

        # Update the file
        with open(self.path, "w") as handle:
            toml.dump(self.content, handle)
