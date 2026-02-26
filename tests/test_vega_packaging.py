"""Tests for the update_semantic_version python file to confirm that the features of the workflow work as
intended.

These tests are intended to be ran using pytest
"""
import os
import re
import tempfile
import datetime
import shutil
import json

import toml
import pytest

from vega.packaging import commits
from vega.packaging import factory
from vega.packaging import const
from vega.packaging import versions
from vega.packaging.bootstrappers import update_semantic_version


@pytest.fixture
def changelog_path():
    """Temporary changelog.md file for testing"""
    path = os.path.join(tempfile.tempdir, "changelog.md")
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def pyproject_path():
    """Temporary pyproject.toml file for testing"""
    path = os.path.join(tempfile.tempdir, "pyproject.toml")
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def dockerfile_path():
    """Temporary Dockerfile file for testing"""
    path = os.path.join(tempfile.tempdir, "Dockerfile")
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def githubenv_path():
    """Gets the location of the github env file and creates a temporary path if it doesn't"""
    delete_file = "GITHUB_ENV" not in os.environ
    path = os.environ.get("GITHUB_ENV", os.path.join(tempfile.tempdir, "set_env_86bd2d54-09b3-476f-8235-5936444c37fa"))
    yield path
    if delete_file and os.path.exists(path):
        os.remove(path)


@pytest.fixture
def react_package_path():
    """Temporary react package.json file for testing"""
    path = os.path.join(tempfile.tempdir, "package.json")
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_python_project():
    """Temporary package directory file for testing."""
    path = os.path.join(tempfile.tempdir, "test_python_packaging")
    pyproject_path = os.path.join(path, "pyproject.toml")
    if not os.path.exists(path):
        os.mkdir(path)
        with open(pyproject_path, "w+") as handle:
            handle.write("""[build-system]
requires = [ "setuptools >= 61.0",]
build-backend = "setuptools.build_meta"

[project]
name = "vega-packaging"
version = "0.0.0"
""")

    yield path
    if os.path.exists(path):
        shutil.rmtree(path)


@pytest.fixture
def temp_react_project():
    """Temporary package directory file for testing."""
    path = os.path.join(tempfile.tempdir, "test_react_packaging")
    pyproject_path = os.path.join(path, "package.json")
    if not os.path.exists(path):
        os.mkdir(path)
        with open(pyproject_path, "w+") as handle:
            handle.write("""{
  "name": "test_project",
  "private": true,
  "version": "0.0.0",
  "type": "module"
  }
""")

    yield path
    if os.path.exists(path):
        shutil.rmtree(path)


# ============================================================================
# Tests for const.py
# ============================================================================

def test_versions_enum():
    """Test that the Versions enum has the expected values"""
    assert const.Versions.MAJOR.value == 0
    assert const.Versions.MINOR.value == 1
    assert const.Versions.PATCH.value == 2


def test_changes_enum():
    """Test that the Changes enum has all changelog categories"""
    assert const.Changes.ADDED.value == "added"
    assert const.Changes.CHANGED.value == "changed"
    assert const.Changes.DEPRECATED.value == "deprecated"
    assert const.Changes.REMOVED.value == "removed"
    assert const.Changes.FIXED.value == "fixed"
    assert const.Changes.SECURITY.value == "security"
    assert const.Changes.UPDATED.value == "changed"


def test_build_types_enum():
    """Test that the BuildTypes enum has the expected values"""
    assert const.BuildTypes.PYTHON.value == "python"
    assert const.BuildTypes.NPM.value == "npm"
    assert const.BuildTypes.DOCKER.value == "docker"


# ============================================================================
# Tests for versions.py
# ============================================================================

def test_semantic_version_init():
    """Test SemanticVersion initialization and string conversion"""
    sv = versions.SemanticVersion("1.2.3")
    assert str(sv) == "1.2.3"


def test_semantic_version_bump_patch():
    """Test SemanticVersion patch bump"""
    sv = versions.SemanticVersion("0.1.0")
    result = sv.bump(const.Versions.PATCH)
    assert result == "0.1.1"
    assert str(sv) == "0.1.1"


def test_semantic_version_bump_minor():
    """Test SemanticVersion minor bump"""
    sv = versions.SemanticVersion("0.0.1")
    result = sv.bump(const.Versions.MINOR)
    assert result == "0.1.0"
    assert str(sv) == "0.1.0"


def test_semantic_version_bump_major():
    """Test SemanticVersion major bump"""
    sv = versions.SemanticVersion("0.1.1")
    result = sv.bump(const.Versions.MAJOR)
    assert result == "1.0.0"
    assert str(sv) == "1.0.0"


def test_semantic_version_has_changed():
    """Test SemanticVersion change detection"""
    sv = versions.SemanticVersion("1.0.0")
    assert not sv.has_changed()
    sv.bump(const.Versions.PATCH)
    assert sv.has_changed()


def test_semantic_version_start_value():
    """Test SemanticVersion original value tracking"""
    sv = versions.SemanticVersion("1.2.3")
    sv.bump(const.Versions.MINOR)
    assert sv.start_value() == "1.2.3"
    assert str(sv) == "1.3.0"


# ============================================================================
# Tests for commits.py
# ============================================================================

def test_commit_message_breakdown():
    """Test that the parsing of the commit message works as expected under different scenarios"""
    # Test simple commit message
    # Note: UPDATED is an alias for CHANGED (same enum value), so Python uses CHANGED as the canonical name
    message = commits.CommitMessage("#updated an update", default_bump=const.Versions.MINOR)
    assert message.date == datetime.datetime.today().strftime("%Y/%m/%d %H:%M:%S")
    assert message.changes == {"CHANGED": ["an update"]}
    assert message.semantic_version_bump == const.Versions.MINOR

    # Test setting a different version bump from default
    message = commits.CommitMessage("#patch #fixed fixed hello_world.py")
    assert message.changes == {"FIXED": ["fixed hello_world.py"]}
    assert message.semantic_version_bump == const.Versions.PATCH

    # Test setting multiple comments and setting bump to be a major bump
    message = commits.CommitMessage("#major #added added hello_world.py"
                                    "#removed removed bad vibes")
    assert message.changes == {"ADDED": ["added hello_world.py"],
                               "REMOVED": ["removed bad vibes"]}
    assert message.semantic_version_bump == const.Versions.MAJOR


def test_message_markdown():
    """Tests that the markdown string gets generated as expected from the changelog dict"""
    message = commits.CommitMessage("testing in pytest", "06/24/2024 12:02:11", auto_parse=False)
    message.changes = {"ADDED": ["added hello_world.py", "better vibes"],
                       "REMOVED": ["removed bad vibes"]}
    markdown = message.markdown("0.1.1")
    assert markdown == ("## [0.1.1] - 06/24/2024 12:02:11\n\n"
                        "### Added\n\n"
                        "- added hello_world.py\n"
                        "- better vibes\n\n"
                        "### Removed\n\n"
                        "- removed bad vibes\n\n\n")


def test_parser_factory():
    changelog_cls = factory.get_parser_from_path("changelog.md")
    assert changelog_cls.FILENAME_REGEX.pattern == "CHANGELOG.md"

    changelog_cls = factory.get_parser_from_path("pyproject.toml")
    assert changelog_cls.FILENAME_REGEX.pattern == "pyproject.toml"


# ============================================================================
# Tests for parsers
# ============================================================================

def test_changelog_parser(changelog_path):
    """Tests that the changelog parser works as expected"""
    message = commits.CommitMessage("#major #added added hello_world.py"
                                    "#removed removed bad vibes")

    changelog_parser = factory.get_parser_from_path(changelog_path)
    assert changelog_parser.FILENAME_REGEX.match("CHANGELOG.md") is not None

    assert not changelog_parser.exists
    changelog_parser.update(message, None)
    assert changelog_parser.exists

    content = [changelog_parser.TEMPLATE, message.markdown("1.0.0")]
    with open(changelog_parser.path, "r") as handle:
        assert handle.read() == "\n".join(content)

    # Run a second check to confirm that the message is getting added properly
    message = commits.CommitMessage("#security checking that we don't add the same line at the end. #minor")
    # This will generate a new parser object as the object generation isn't cached
    changelog_parser = factory.get_parser_from_path(changelog_path)

    assert changelog_parser.exists
    changelog_parser.update(message, "1.0.0")

    content.insert(1, f"\n{message.markdown('1.1.0')}")
    with open(changelog_parser.path, "r") as handle:
        assert handle.read() == "".join(content)


def test_pyproject_parser(pyproject_path):
    """Tests that the pyproject parser works as expected"""
    message = commits.CommitMessage("#major #added added hello_world.py"
                                    "#removed removed bad vibes")


    pyproject_parser = factory.get_parser_from_path(pyproject_path)
    assert pyproject_parser.FILENAME_REGEX.match("pyproject.toml") is not None
    assert not pyproject_parser.exists
    pyproject_parser.create()
    assert pyproject_parser.exists
    pyproject_parser.update(message, None)

    with open(pyproject_parser.path, "r") as handle:
        content = toml.load(handle)
        assert content["project"]["version"] == "1.0.0"


def test_dockerfile_parser(dockerfile_path):
    """Tests that the Dockerfile parser works as expected"""
    dockerfile_parser = factory.get_parser_from_path(dockerfile_path)
    assert dockerfile_parser.FILENAME_REGEX.match("Dockerfile") is not None
    assert not dockerfile_parser.exists
    dockerfile_parser.create()
    assert dockerfile_parser.exists

    # DockerFile doesn't have version tracking
    assert dockerfile_parser.version is None
    assert dockerfile_parser.HAS_VERSION is False
    assert dockerfile_parser.IS_BUILD_FILE is True
    assert dockerfile_parser.BUILD_TYPE == const.BuildTypes.DOCKER

    # Test that update raises NotImplementedError
    message = commits.CommitMessage("#major #added added dockerfile support")
    with pytest.raises(NotImplementedError):
        dockerfile_parser.update(message, None)


def test_github_env_parser(githubenv_path):
    """Tests that the github env parser works as expected"""
    message = commits.CommitMessage("#major #added added hello_world.py"
                                    "#removed removed bad vibes")


    githubenv_parser = factory.get_parser_from_path(githubenv_path)
    assert githubenv_parser.FILENAME_REGEX.pattern == "set_env_[a-z0-9-]+"
    # As these tests may be run outside a GitHub workflow environments, the files may not exist
    if not githubenv_parser.exists:
        githubenv_parser.create()
    assert githubenv_parser.exists
    githubenv_parser.update(message, None)

    with open(githubenv_parser.path, "r") as handle:
        content = handle.read()
        assert re.search("SEMANTIC_VERSION=1.0.0", content) is not None


def test_react_package_parser(react_package_path):
    """Tests that the react package parser works as expected"""
    message = commits.CommitMessage("#major #added added hello_world.py"
                                    "#removed removed bad vibes")

    react_package_parser = factory.get_parser_from_path(react_package_path)
    assert react_package_parser.FILENAME_REGEX.match("package.json") is not None
    assert not react_package_parser.exists
    react_package_parser.create()
    assert react_package_parser.exists
    react_package_parser.update(message, None)


    with open(react_package_parser.path, "r+", encoding="utf-8") as handle:
        content = json.load(handle)
        assert content["version"] == "1.0.0"


# ============================================================================
# Integration tests
# ============================================================================

def test_update_semantic_version_python(temp_python_project):
    """ Integration test to confirm that the code that makes up the 'update_semantic_version' cli command works on
    a deployable python package."""

    message_str = "#minor #security passed test_update_semantic_version"
    paths = [os.path.join(temp_python_project, filename) for filename in os.listdir(temp_python_project)]

    # Adding changelog path to test the autocreation
    paths.append(os.path.join(temp_python_project, "CHANGELOG.md"))

    update_semantic_version.update_semantic_version(message_str, paths)

    # Check generated files
    message = commits.CommitMessage(message_str)

    # Check changelog.md
    changelog_path = os.path.join(temp_python_project, "changelog.md")
    changelog_cls = factory.get_parser_cls_by_filename("changelog.md")

    content = f"{changelog_cls.TEMPLATE}\n{message.markdown('0.1.0')}"
    with open(changelog_path, "r") as handle:
        assert handle.read() == content

    # Check pyproject.toml
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")

    with open(pyproject_path, "r") as handle:
        assert toml.load(handle)["project"]["version"] == "0.1.0"


def test_update_semantic_version_react(temp_react_project):
    """ Integration test to confirm that the code that makes up the 'update_semantic_version' cli command works on
    a deployable react package."""

    message_str = "#minor #security passed test_update_semantic_version"
    paths = [os.path.join(temp_react_project, filename) for filename in os.listdir(temp_react_project)]

    # Adding changelog path to test the autocreation
    paths.append(os.path.join(temp_react_project, "CHANGELOG.md"))

    update_semantic_version.update_semantic_version(message_str, paths)

    # Check generated files
    message = commits.CommitMessage(message_str)

    # Check changelog.md
    changelog_path = os.path.join(temp_react_project, "changelog.md")
    changelog_cls = factory.get_parser_cls_by_filename("changelog.md")

    content = f"{changelog_cls.TEMPLATE}\n{message.markdown('0.1.0')}"
    with open(changelog_path, "r") as handle:
        assert handle.read() == content

    # Check pyproject.toml
    pyproject_path = os.path.join(temp_react_project, "package.json")

    with open(pyproject_path, "r") as handle:
        assert json.load(handle)["version"] == "0.1.0"
