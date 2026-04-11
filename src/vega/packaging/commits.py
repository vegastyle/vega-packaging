"""Python module for parsing commit messages and updating semantic version.

This module uses features of the enum module only available in python 3.12 and higher
"""
import logging
import datetime
import enum
import re

from vega.packaging import const

logger = logging.getLogger(__name__)


class CommitMessage:
    """Parses a commit message from a version control system."""

    def __init__(self, message: str, date: str = None, auto_parse: bool = True, default_bump: const.Versions = None):
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
        self._bump = default_bump

        self.semantic_version_bump = None
        self.publish_tags = None
        self.publish = False
        self.release = False
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
    def is_valid(self) -> bool:
        """Checks if the message string is valid for updating the semantic version.

        Returns:
            bool: True if the message is valid, False otherwise.
        """
        return "#" in self.__message and "#ignore" not in self.__message.lower()

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
                tag_enum = (getattr(const.Versions, tag, None) or
                            getattr(const.Changes, tag.upper(), None) or
                            getattr(const.WorkflowTypes, tag.upper(), None))

                if isinstance(tag_enum, const.Versions) and (self.semantic_version_bump is None or tag_enum.value < self.semantic_version_bump.value):
                    self.semantic_version_bump = tag_enum

                elif isinstance(tag_enum, const.Changes):
                    key = tag_enum.name

                elif isinstance(tag_enum, const.WorkflowTypes):
                    if tag_enum == const.WorkflowTypes.PUBLISH:
                        self.publish = True
                    elif tag_enum == const.WorkflowTypes.RELEASE:
                        self.release = True

                continue

            if key is not None and message_section:
                self.changes.setdefault(key, []).append(message_section.strip())

        # Fall back to default bump if no version tag was found
        if self.semantic_version_bump is None:
            self.semantic_version_bump = self._bump

    def markdown(self, semantic_version) -> str:
        """Converts the changelog dict into a markdown string that follows the Keep A Changelog Format."""
        # Add new header section for the latest updates
        content = [f"## [{semantic_version}] - {self.date}"]
        # Add list of changes
        for change_section in const.Changes:
            if change_section.name in self.changes:
                content.append(f"\n### {change_section.value.capitalize()}\n")
                for change in self.changes[change_section.name]:
                    content.append(f"- {change}")
        content.append("\n\n")  # Create an extra buffer between new change logs
        return "\n".join(content)