"""Module for holding the code for parsing the Dockerfile files"""
import json
import os
import re
import subprocess
import logging

from vega.packaging import const
from vega.packaging import contextmanagers
from vega.packaging.parsers import abstract_parser

logger = logging.getLogger(__name__)

class DockerFile(abstract_parser.AbstractFileParser):
    """Parser and builder for dockerfiles"""
    FILENAME_REGEX = re.compile("dockerfile", re.I)
    TEMPLATE = ""
    PRIORITY = 2
    HAS_VERSION = False 
    IS_BUILD_FILE = True
    BUILD_TYPE=const.BuildTypes.DOCKER

    def __init__(self, path, version = None):
        super().__init__(path, version)
        # is this current file inside a folder structure that is versioned by git
        self.__in_git_repository = False

    def __get_git_repository(self):
        """Get the git repository name if the Dockerfile is inside a Git repo."""
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
            )
        if result.returncode != 0:
            return None
        return os.path.basename(result.stdout.strip())

    def __get_docker_repositories(self):
        """Get list of Docker registries the user is logged into from Docker config."""
        config_path = os.path.expanduser("~/.docker/config.json")
        if not os.path.exists(config_path):
            return []

        with open(config_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)

        return sorted(config.get("auths", {}).keys())

    def __get_image_tags(self):
        """Get available tags for the image from the registry."""
        if not self.registry or not self.package:
            return []

        try:
            with contextmanagers.WorkingDirectory(self.path, is_file=True):
                result = subprocess.run(
                    ["docker", "images", "--format", "{{.Tag}}", f"{self.registry}/{self.package}"],
                    capture_output=True,
                    text=True,
                )
            if result.returncode != 0:
                return []
            return [tag.strip() for tag in result.stdout.strip().split("\n") if tag.strip()]
        except Exception:
            return []

    def __get_image_semantic_versions(self):
        """Get available semantic versions from the repository ordered from newest to oldest"""
        tags = self.__get_image_tags()
        versions = [
            tag for tag in tags
            if re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", tag)
        ]
        versions.sort(
            key=lambda value: [int(part) for part in value.split(".")],
            reverse=True,
        )
        return versions

    @property
    def version(self) -> str:
        """The semantic version parsed from this file."""
        if not self._version: 
            versions = self.__get_image_semantic_versions() or ["0.0.0"]
            self._version = versions[0]
        return self._version

    @property
    def content(self) -> dict:
        """The contents of this dockerfile"""
        return super(DockerFile, self).content or {}

    @property
    def package(self) -> str: 
        """ The name of the package that this file defines if it is file that defines a package build"""
        if not self._package:
            #if git is available, grab repository name
            self._package = self.__get_git_repository() or os.path.basename(os.path.dirname(self.path))
            #else  use parent package name 
        return self._package
    
    @package.setter
    def package(self, value):
        self._package = value

    @property
    def registry(self):
        """The name of the registry where the package this file belongs to gets published to"""
        if not self._registry:
            docker_repositories = self.__get_docker_repositories()
            if len(docker_repositories) > 1:
                raise ValueError("Too many repositories to infer registry to target. Provide a specific repository to target")
            if docker_repositories:
                self._registry = docker_repositories[0]
        return self._registry
    
    @registry.setter
    def registry(self, value=None):
        """ The name of the registry where the package this file belongs to gets published to""" 
        self._registry = value

    @property
    def tag(self):
        if not self.registry or not self.package:
            return None
        return f"{self.registry}/{self.package}:{self.version}"
    
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
        logger.warning("Updating DockerFile is not supported")

    def build(self, commit_message=None):
        """Builds the Docker image."""
        if not self.tag:
            raise RuntimeError("Registry must be set before building")
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            result = subprocess.run(
                ["docker", "build", "-t", self.tag, "."],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Docker build failed: {result.stderr}")
            self._build = self.tag

    def publish(self, registry=None):
        """Pushes the Docker image to registry."""
        if not self._build:
            raise RuntimeError("Must build before publishing")
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            result = subprocess.run(
                ["docker", "push", self._build],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Docker push failed: {result.stderr}")
