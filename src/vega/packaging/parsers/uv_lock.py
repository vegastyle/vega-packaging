"""Module for holding the code for keeping a uv.lock file in step with the version bump"""

import logging
import re

from vega.packaging import commits, versions
from vega.packaging.parsers import abstract_parser

logger = logging.getLogger(__name__)


class UvLock(abstract_parser.AbstractFileParser):
    """Parser for uv.lock files.

    uv records the project being locked as a package whose source is the project directory,
    ``source = { editable = "." }``. When pyproject.toml's version is bumped, that entry's
    ``version`` line goes stale, and the next ``uv run`` rewrites the lock in the working
    tree. This parser rewrites only that one line, in place: every other byte, line endings
    included, stays as uv wrote it, and nothing is re-resolved, so no network access or
    credentials for private dependencies are needed. A workspace root (``source = { virtual =
    "." }``) carries no version and is left alone.
    """

    NAME = "UvLock"
    FILENAME_REGEX = re.compile(r"^uv\.lock$")
    # After the files that own the version (pyproject.toml is 1), so it never sets it.
    PRIORITY = 4
    # The project's own entry: its name, then the version line the bump rewrites.
    PROJECT_ENTRY = re.compile(
        r'^\[\[package\]\]\r?\nname = "(?P<name>[^"]+)"\r?\n'
        r'version = "(?P<version>[^"]+)"\r?\nsource = \{ editable = "\." \}',
        re.MULTILINE,
    )

    @property
    def entry(self) -> re.Match | None:
        """The project's own entry in the lock, or None when the project has no version."""
        return self.PROJECT_ENTRY.search(self.content or "")

    @property
    def version(self) -> versions.SemanticVersion | None:
        """The project's version as the lock records it."""
        if not self._version and self.entry:
            self._version = versions.SemanticVersion(self.entry["version"])
        return self._version

    @property
    def package(self) -> str:
        """The name of the project the lock was made for."""
        if not self._package and self.entry:
            self._package = self.entry["name"]
        return self._package

    def read(self) -> str:
        """Reads the lock as text, keeping its line endings."""
        with open(self.path, "r", encoding="utf-8", newline="") as handle:
            return handle.read()

    def update(
        self,
        commit_message: commits.CommitMessage,
        semantic_version: versions.SemanticVersion | str,
    ):
        """Bumps the project's locked version the same way pyproject.toml's is bumped.

        Args:
            commit_message: the message to use for updating this file.
            semantic_version: the version the other packaging files start from, if any.
        """
        entry = self.entry
        if not entry:
            logger.info(
                f"{self.path} records no project version; nothing to keep in step"
            )
            return
        super().update(commit_message, semantic_version)
        start, end = entry.span("version")
        content = f"{self.content[:start]}{self.version}{self.content[end:]}"
        with open(self.path, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        self._content = content
