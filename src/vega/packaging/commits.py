"""Python module for parsing commit messages and updating semantic version.

This module uses features of the enum module only available in python 3.12 and higher
"""
import logging
import datetime
import enum
import re

logger = logging.getLogger(__name__)


class Versions(enum.Enum):
    """ Enums for the different semantic verions"""
    MAJOR = 0
    MINOR = 1
    PATCH = 2


class Changes(enum.Enum):
    """Enum for the different possible changelog categories as determined by Keepchangelog.com"""
    # Keepchangelog.com standard changes
    ADDED = "added"
    CHANGED = "changed"
    DEPRECATED = "deprecated"
    REMOVED = "removed"
    FIXED = "fixed"
    SECURITY = "security"

    # Custom tags for indicating other changes
    UPDATED = "changed"


class CommitMessage:
    """Parses a commit message from a version control system."""

    def __init__(self, message: str, date: str = None, auto_parse: bool = True, default_bump: Versions = None):
        """Constructor

        Args:
            message: The message sent to the source control to parse into a changelog dictionary
            date: The date in year-month-day format for when the changelog was created.
              If not provided it will default to today's date.
            auto_parse: automatically parse the message for data
            default_bump: the default to set for bumping the version number. Defaults to None.
        """
        self.__message = message
        self.__date = date or datetime.datetime.today().strftime("%Y/%m/%d %H:%M:%S")

        self.semantic_version = None
        self.bump = default_bump
        self.changes = {}

        if auto_parse:
            self.parse()

    @property
    def message(self) -> str:
        """The message to parse"""
        return self.__message

    @property
    def date(self) -> str:
        """The date that the message was authored"""
        return self.__date

    @property
    def markdown(self) -> str:
        """Converts the changelog dict into a markdown string that follows the Keep A Changelog Format."""
        # Add new header section for the latest updates
        content = [f"## [{self.semantic_version}] - {self.date}"]
        # Add list of changes
        for change_section in Changes:
            if change_section in self.changes:
                content.append(f"\n### {change_section.value.capitalize()}\n")
                for change in self.changes[change_section]:
                    content.append(f"- {change}")
        content.append("\n\n")  # Create an extra buffer between new change logs
        return "\n".join(content)

    def parse(self):
        """Parses the commit message from a version control system and to get the messages that make it up.

        The message doesn't have the version number and must be parsed from another location.
        """
        key = None

        # Parse the message to determine the values to add to the changelog dict
        message_sections = re.split("(#[a-z0-9]+)", self.__message)
        for message_section in message_sections:

            if message_section.startswith("#"):
                key = None
                tag = message_section[1:].upper()
                if getattr(Versions, tag, None) in Versions:
                    self.bump = getattr(Versions, tag)

                elif getattr(Changes, tag, None) in Changes:
                    key = getattr(Changes, tag.upper())

                continue

            if key in Changes and message_section:
                self.changes.setdefault(key, []).append(message_section.strip())

    def bump_semantic_version(self):
        """Helper method for bumping the internal semantic version number.

        Using this method consumes the value of bump and sets it back to None
        """
        if not self.semantic_version:
            raise ValueError("No value set for the semantic version associated with this commit message")

        self.semantic_version = bump_semantic_version(self.semantic_version, self.bump)
        self.bump = None


def bump_semantic_version(current_version: str, version_bump: enum.Enum) -> str:
    """
    Bumps the current semantic version number

    Arg:
        current_version (str): The current semantic version that needs to be updated.
                               Expects the format to be [major].[minor].[patch].
        version_bump (str): The version number to bump. Expects the values 'major', 'minor', 'patch'.

    Return:
        str
    """
    logger.debug(f"Performing {version_bump.name.lower()} bump")
    version_numbers = current_version.split(".")

    for index, value in enumerate(version_numbers[version_bump.value:]):
        version_index = version_bump.value + index
        if not index:
            # Bump the value of the given version category
            version_numbers[version_index] = str(int(value) + 1)
            continue
        # Reset any version categories that follow to zero
        version_numbers[version_index] = "0"

    resolved_version = ".".join(version_numbers)
    logger.debug(f"Bumped semantic version to {resolved_version}")
    return resolved_version
