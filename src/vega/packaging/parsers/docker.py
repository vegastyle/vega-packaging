"""Module for holding the code for parsing the Dockerfile files"""
import os
import re
import subprocess

from vega.packaging import const
from vega.packaging import contextmanagers
from vega.packaging.parsers import abstract_parser


class DockerFile(abstract_parser.AbstractFileParser):
    """Parser for docker-compose.yaml files"""
    FILENAME_REGEX = re.compile("dockerfile", re.I)
    TEMPLATE = ""
    PRIORITY = 5
    HAS_VERSION = False 
    IS_BUILD_FILE = True
    BUILD_TYPE=const.BuildTypes.DOCKER

    def __set_build_path(self, registry, registry_version):
        self._build = f"{registry}/{self.package}:{registry_version}"

    @property
    def version(self) -> str:
        """The semantic version parsed from this file."""
        return None

    @property
    def content(self) -> dict:
        """The contents of this docker-compose.yaml file"""
        return super(DockerFile, self).content or {}

    @property
    def package(self) -> str: 
        """ The name of the package that this file defines if it is file that defines a package build"""
        if not self._package:
            self._package = os.path.basename(os.path.dirname(self.path))
        return self._package
    
    @property
    def registry(self):
        """ The name of the registry where the package this file belongs to gets published to""" 
        return self._registry
    
    @registry.setter
    def registry(self, value=None):
        """ The name of the registry where the package this file belongs to gets published to""" 
        self._registry = value
        self.__set_build_path(self._registry, self._registry_version)

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
        self.__set_build_path(self._registry, self._registry_version or self.version)

    def create(self):
        """Creates a changelog file if it doesn't exist with some default values."""
        with open(self.path, "w") as handle:
            handle.write(self.TEMPLATE)

    def read(self) -> list:
        """Reads the dockerfile file."""
        with open(self.path, "r") as handle:
            return list(handle.readlines())

    def update(self, *args) -> list:
        """Updates the dockerfile file."""
        raise NotImplementedError("This method is not implemented")      
        
    def build(self, commit_message=None):
        """Builds the Docker image."""
        if not self._build:
            raise RuntimeError("Registry must be set before building")
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            result = subprocess.run(
                ["docker", "build", "-t", self._build, "."],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Docker build failed: {result.stderr}")

    def publish(self, registry=None):
        """Pushes the Docker image to registry."""
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            if not self._build:
                raise RuntimeError("Must build before publishing")
            result = subprocess.run(
                ["docker", "push", self._build],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Docker push failed: {result.stderr}")