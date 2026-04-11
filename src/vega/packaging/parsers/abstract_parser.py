"""Module for holding the abstract file parser class"""
import os
import logging

from vega.packaging import commits, versions


logger = logging.getLogger(__name__)


class AbstractFileParser:
    """Abstract file parser class for creating new file parsers."""
    FILENAME_REGEX = None
    TEMPLATE = None
    AUTOCREATE = False
    DEFAULT_VERSION = "0.0.0"
    PRIORITY = 5
    HAS_VERSION = True
    IS_BUILD_FILE = False
    BUILD_TYPE = None
    RELEASE_PATH = None

    def __init__(self, path: str, version: versions.SemanticVersion =None):
        """Constructor

        Args:
            path: path to the file being parsed
        """
        self.__path = path
        self._content = None
        self._version = version
        self._build = None
        self._registry = None
        self._registry_version = None
        self._package = None

    @property
    def path(self) -> str:
        """The path to the file that is being parsed"""
        return self.__path

    @property
    def filename(self) -> str:
        """Name of the file being parsed."""
        return os.path.basename(self.__path)


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
    def registry(self):
        """ The name of the registry where the package this file belongs to gets published to""" 
        return self._registry
    
    @registry.setter
    def registry(self, value=None):
        """ The name of the registry where the package this file belongs to gets published to""" 
        self._registry = value

    @property
    def registry_version(self):
        """ The version to use when publishing to the registry, this maybe different from the version of the file.
        Defaults to the file version
        """ 
        return self._registry_version or self.version
    
    @registry_version.setter
    def registry_version(self, value=None):
        """ The name of the registry where the package this file belongs to gets published to""" 
        self._registry_version = value

    @property
    def package(self) -> str: 
        """ The name of the package that this file belongs to"""
        raise NotImplementedError("This abstract method needs to be reimplemented")

    @property
    def version(self) -> str:
        """The semantic version parsed from this file"""
        raise NotImplementedError("This abstract method needs to be reimplemented")

    @version.setter
    def version(self, value):
        self._version = value

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

    def update(self, commit_message: commits.CommitMessage, semantic_version: versions.SemanticVersion|str):
        """Updates the data of the file"""
        if semantic_version: 
            self._version = versions.SemanticVersion(semantic_version)
        self.version.bump(commit_message.semantic_version_bump)

    def build(self, version=None, registry=None):
        """Builds a package that uses this file"""
        raise NotImplementedError("This abstract method needs to be reimplemented")
    
    def publish(self, version=None, registry=None):
        """Publishes this file to a repository"""
        raise NotImplementedError("This abstract method needs to be reimplemented")

    def release(self, version=None, registry=None):
        """Publishes this file to github as a release. Requires the build step to complete."""
        raise NotImplementedError("This abstract method needs to be reimplemented")