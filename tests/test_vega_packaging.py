"""Tests for the update_semantic_version python file to confirm that the features of the workflow work as
intended.

These tests are intended to be ran using pytest
"""
import os
import tempfile
import datetime

import toml
import pytest

from vega.packaging import commits
from vega.packaging import factory


@pytest.fixture
def changelog_path():
    path = os.path.join(tempfile.tempdir, "changelog.md")
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def pyproject_path():
    path = os.path.join(tempfile.tempdir, "pyproject.toml")
    yield path
    if os.path.exists(path):
        os.remove(path)


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
    changelog_cls = factory.get_parser_by_filename("changelog.md")
    assert changelog_cls.FILENAME == "CHANGELOG.md"

    changelog_cls = factory.get_parser_by_filename("pyproject.toml")
    assert changelog_cls.FILENAME == "pyproject.toml"


def test_changelog_parser(changelog_path):
    """Tests that the changelog parser works as expected"""
    _, filename = os.path.split(changelog_path)
    changelog_cls = factory.get_parser_by_filename(filename)
    assert changelog_cls.FILENAME == "CHANGELOG.md"
    message = commits.CommitMessage("#major #added added hello_world.py"
                                    "#removed removed bad vibes")
    changelog_parser = changelog_cls(changelog_path)
    assert not changelog_parser.exists
    changelog_parser.update(message)
    assert changelog_parser.exists

    content = f"{changelog_cls.TEMPLATE}\n{message.markdown}"
    with open(changelog_parser.path, "r") as handle:
        assert handle.read() == content

def test_pyproject_parser(pyproject_path):
    """Tests that the pyproject parser works as expected"""
    _, filename = os.path.split(pyproject_path)
    pyproject_cls = factory.get_parser_by_filename(filename)
    assert pyproject_cls.FILENAME == "pyproject.toml"
    message = commits.CommitMessage("#major #added added hello_world.py"
                                    "#removed removed bad vibes")
    pyproject_parser = pyproject_cls(pyproject_path)
    assert not pyproject_parser.exists
    pyproject_parser.create()
    assert pyproject_parser.exists
    pyproject_parser.update(message)

    with open(pyproject_parser.path, "r") as handle:
        content = toml.load(handle)
        assert content["project"]["version"] == message.semantic_version


