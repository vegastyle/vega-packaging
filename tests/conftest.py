"""Pytest configuration for test startup."""

from __future__ import annotations

import os
from pathlib import Path


def _parse_env_line(line: str) -> tuple[str, str] | None:
    """Parse a single KEY=VALUE line from a .env file."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export "):].strip()
    if "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()

    if value and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]

    return key, value


def _load_repo_env() -> None:
    """Load the repository .env into the current process for subprocess-based tests."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(line)
        if parsed is None:
            continue
        key, value = parsed
        os.environ.setdefault(key, value)

    # Keep compatibility with the existing .env spelling.
    if "TWINE_USERNAME" not in os.environ and "TWINE_USENAME" in os.environ:
        os.environ["TWINE_USERNAME"] = os.environ["TWINE_USENAME"]


def pytest_configure() -> None:
    """Load environment variables before tests are collected or executed."""
    _load_repo_env()
