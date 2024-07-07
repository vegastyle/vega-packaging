"""Module for holding the abstract file parser class"""
import os

from vega.packaging import commits


class AbstractFileParser:
    """Abstract file parser class for creating new file parsers."""
    FILENAME_REGEX = None
    TEMPLATE = None
    AUTOCREATE = True
    DEFAULT_VERSION = "0.0.0"
    PRIORITY = 5

    def __init__(self, path: str):
        """Constructor

        Args:
            path: path to the file being parsed
        """
        self.__path = path
        self._content = None
        self._version = None

    @property
    def path(self) -> str:
        """The path to the file that is being parsed"""
        return self.__path

    @property
    def exists(self) -> bool:
        """ Does this file exist on disk"""
        return os.path.exists(self.__path)

    @property
    def content(self):
        """The contents of this pyproject.toml file"""
        if not self._content and self.exists:
            self._content = self.read()
        return self._content

    @property
    def version(self) -> str:
        """The semantic version parsed from this file"""
        raise NotImplementedError("This abstract method needs to be reimplemented")

    def reset(self):
        """Resets the values of the object so they get parsed again.

        This class uses simple implementation of lazy loading to avoid parsing files until the data is needed.
        """
        self._content = None
        self._version = None

    def create(self):
        """Creates the file on disk with some default values."""
        raise NotImplementedError("This abstract method needs to be reimplemented")

    def read(self):
        """Reads the file on disk."""
        raise NotImplementedError("This abstract method needs to be reimplemented")

    def update(self, commit_message: commits.CommitMessage):
        """Updates the data of the file"""
        raise NotImplementedError("This abstract method needs to be reimplemented")

    def update_version(self, commit_message: commits.CommitMessage):
        """Updates the semantic version value of this file based on the data of the commit message.

        If the commit message does not have a semantic version, the value parsed from this file is used instead.
        If the commit message has a pending version bump, that version bump is applied.
        """
        if not commit_message.semantic_version and self.version:
            commit_message.semantic_version = self.version

        elif not commit_message.semantic_version:
            commit_message.semantic_version = self.DEFAULT_VERSION
            commit_message.bump = commit_message.bump or commits.Versions.MINOR

        if commit_message.bump:
            commit_message.bump_semantic_version()

        self._version = commit_message.semantic_version
