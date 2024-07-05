"""Tests for the update_semantic_version python file to confirm that the features of the workflow work as
intended.

These tests are intended to be ran using pytest.pyproject.toml
"""
import datetime

from vega.packaging import commits
from vega.packaging import factory


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
