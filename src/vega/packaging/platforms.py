"""Module for platform-specific release providers."""
import subprocess

from vega.packaging import const


class AbstractPlatform:
    def __init__(self, cwd: str):
        self._cwd = cwd

    def create(self, version: str, notes: str, files: list[str] | None = None):
        raise NotImplementedError

    @property
    def last_release(self) -> str | None:
        raise NotImplementedError


class Github(AbstractPlatform):
    def create(self, version: str, notes: str, files: list[str] | None = None):
        cmd = ["gh", "release", "create", f"v{version}",
               "--title", f"v{version}", "--notes", notes]
        if files:
            cmd.extend(files)
        result = subprocess.run(cmd, cwd=self._cwd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Release failed: {result.stderr}")

    @property
    def last_release(self) -> str | None:
        result = subprocess.run(
            ["gh", "release", "list", "--limit", "1", "--json", "tagName",
             "--jq", ".[0].tagName"],
            cwd=self._cwd, capture_output=True, text=True
        )
        tag = result.stdout.strip()
        return tag.lstrip("v") if tag else None


def get(name: str | const.Platforms, cwd: str) -> AbstractPlatform:
    _map = {const.Platforms.GITHUB: Github}
    if isinstance(name, str):
        name = const.Platforms(name.lower())
    cls = _map.get(name)
    if cls is None:
        raise ValueError(f"Unknown platform: {name!r}. Available: {[p.value for p in _map]}")
    return cls(cwd)
