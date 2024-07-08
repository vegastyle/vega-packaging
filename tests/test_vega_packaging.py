"""Tests for the update_semantic_version python file to confirm that the features of the workflow work as
intended.

These tests are intended to be ran using pytest
"""
import os
import re
import tempfile
import datetime
import shutil

import toml
import pytest

from vega.packaging import commits
from vega.packaging import factory
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
def githubenv_path():
    """Gets the location of the github env file and creates a temporary path if it doesn't"""
    delete_file = "GITHUB_ENV" not in os.environ
    path = os.environ.get("GITHUB_ENV", os.path.join(tempfile.tempdir, "set_env_86bd2d54-09b3-476f-8235-5936444c37fa"))
    yield path
    if delete_file and os.path.exists(path):
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


def test_commit_message_breakdown():
    """Test that the parsing of the commit message works as expected under different scenarios"""
    # Test simple commit message
    message = commits.CommitMessage("#updated an update", default_bump=commits.Versions.MINOR)
    assert message.date == datetime.datetime.today().strftime("%Y/%m/%d %H:%M:%S")
    assert message.changes == {commits.Changes.UPDATED: ["an update"]}
    assert message.bump == commits.Versions.MINOR

    # Test setting a different version bump from default
    message = commits.CommitMessage("#patch #fixed fixed hello_world.py")
    assert message.changes == {commits.Changes.FIXED: ["fixed hello_world.py"]}
    assert message.bump == commits.Versions.PATCH

    # Test setting multiple comments and setting bump to be a major bump
    message = commits.CommitMessage("#major #added added hello_world.py"
                                    "#removed removed bad vibes")
    assert message.changes == {commits.Changes.ADDED: ["added hello_world.py"],
                               commits.Changes.REMOVED: ["removed bad vibes"]}
    assert message.bump == commits.Versions.MAJOR


def test_version_bump():
    """Test that the version bumping logic works as expected"""
    assert commits.bump_semantic_version("0.1.0", version_bump=commits.Versions.PATCH) == "0.1.1"
    assert commits.bump_semantic_version("0.0.1", version_bump=commits.Versions.MINOR) == "0.1.0"
    assert commits.bump_semantic_version("0.1.1", version_bump=commits.Versions.MAJOR) == "1.0.0"


def test_message_markdown():
    """Tests that the markdown string gets generated as expected from the changelog dict"""
    message = commits.CommitMessage("testing in pytest", "06/24/2024 12:02:11", auto_parse=False)
    message.semantic_version = "0.1.1"
    message.changes = {commits.Changes.ADDED: ["added hello_world.py", "better vibes"],
                       commits.Changes.REMOVED: ["removed bad vibes"]}
    assert message.markdown == ("## [0.1.1] - 06/24/2024 12:02:11\n\n"
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


def test_changelog_parser(changelog_path):
    """Tests that the changelog parser works as expected"""
    message = commits.CommitMessage("#major #added added hello_world.py"
                                    "#removed removed bad vibes")

    changelog_parser = factory.get_parser_from_path(changelog_path)
    assert changelog_parser.FILENAME_REGEX.match("CHANGELOG.md") is not None

    assert not changelog_parser.exists
    changelog_parser.update(message)
    assert changelog_parser.exists

    content = [changelog_parser.TEMPLATE, message.markdown]
    with open(changelog_parser.path, "r") as handle:
        assert handle.read() == "\n".join(content)

    # Run a second check to confirm that the message is getting added properly
    message = commits.CommitMessage("#security checking that we don't add the same line at the end. #minor")
    # This will generate a new parser object as the object generation isn't cached
    changelog_parser = factory.get_parser_from_path(changelog_path)

    assert changelog_parser.exists
    changelog_parser.update(message)

    content.insert(1, f"\n{message.markdown}")
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
    pyproject_parser.update(message)

    with open(pyproject_parser.path, "r") as handle:
        content = toml.load(handle)
        assert content["project"]["version"] == message.semantic_version


def test_github_env_parser(githubenv_path):
    """Tests that the pyproject parser works as expected"""
    message = commits.CommitMessage("#major #added added hello_world.py"
                                    "#removed removed bad vibes")


    githubenv_parser = factory.get_parser_from_path(githubenv_path)
    assert githubenv_parser.FILENAME_REGEX.pattern == "set_env_[a-z0-9-]+"
    # As these tests may be run outside a GitHub workflow environments, the files may not exist
    if not githubenv_parser.exists:
        githubenv_parser.create()
    assert githubenv_parser.exists
    githubenv_parser.update(message)

    with open(githubenv_parser.path, "r") as handle:
        content = handle.read()
        assert re.search("SEMANTIC_VERSION=1.0.0", content) is not None

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
    message.semantic_version = "0.1.0"
    
    # Check changelog.md
    changelog_path = os.path.join(temp_python_project, "changelog.md")
    changelog_cls = factory.get_parser_cls_by_filename("changelog.md")

    content = f"{changelog_cls.TEMPLATE}\n{message.markdown}"
    with open(changelog_path, "r") as handle:
        assert handle.read() == content
        
    # Check pyproject.toml
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")

    with open(pyproject_path, "r") as handle:
        assert toml.load(handle)["project"]["version"] == message.semantic_version
