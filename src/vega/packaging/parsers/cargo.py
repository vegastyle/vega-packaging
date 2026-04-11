"""Module for holding the code for parsing the Cargo.toml files"""
import os
import re
import shutil
import subprocess

import toml

from vega.packaging import commits, decorators, const, versions
from vega.packaging.parsers import abstract_parser


class Cargo(abstract_parser.AbstractFileParser):
    """Parser for Cargo.toml files"""
    NAME = "Cargo"
    FILENAME_REGEX = re.compile("cargo.toml", re.I)
    TEMPLATE = {
        "package": {
            "name": None,
            "version": "0.0.0",
            "edition": "2021"
        }
    }
    DEFAULT_REGISTRY = None
    PRIORITY = 1
    IS_BUILD_FILE = True
    BUILD_TYPE = const.BuildTypes.RUST
    RELEASE_PATH = "bin"
    CROSS_TARGETS = {
        "x86_64-unknown-linux-gnu":  "x86_64-linux",
        "aarch64-unknown-linux-gnu": "aarch64-linux",
        "x86_64-apple-darwin":       "x86_64-macos",
        "aarch64-apple-darwin":      "aarch64-macos",
        "x86_64-pc-windows-gnu":     "x86_64-windows",
    }

    @property
    def version(self) -> str:
        """The semantic version parsed from this file."""
        if not self._version:
            self._version = versions.SemanticVersion(self.content.get("package", {}).get("version", self.DEFAULT_VERSION))
        return self._version

    @property
    def content(self) -> dict:
        """The contents of this Cargo.toml file"""
        return super(Cargo, self).content or {}

    @property
    def package(self) -> str:
        """The name of the package that this file defines if it is file that defines a package build"""
        if not self._package:
            self._package = self.read()["package"]["name"]
        return self._package

    def create(self):
        """Creates a Cargo.toml file with some default values."""
        import copy
        content = copy.deepcopy(self.TEMPLATE)
        content["package"]["name"] = os.path.split(os.path.dirname(self.path))[-1]
        content["package"]["version"] = self.DEFAULT_VERSION

        with open(self.path, "w") as handle:
            toml.dump(content, handle)

    def read(self) -> dict:
        """Reads the contents of the Cargo.toml file"""
        return toml.load(self.path)

    @decorators.autocreate
    def update(self, commit_message: commits.CommitMessage, semantic_version: versions.SemanticVersion | str):
        """Updates the contents of the Cargo.toml file with data from the commit message.

        Args:
            commit_message: the message to use for updating this file.
        """
        super(Cargo, self).update(commit_message, semantic_version)

        # Update Cargo.toml version
        self.content["package"]["version"] = str(self.version)

        # Update the file
        with open(self.path, "w") as handle:
            toml.dump(self.content, handle)

    def build(self, commit_message=None):
        """Builds the Rust crate using cargo package."""
        result = subprocess.run(
            ["cargo", "package"],
            cwd=os.path.dirname(self.path),
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Build failed: {result.stderr}")
        package_dir = os.path.join(os.path.dirname(self.path), "target", "package")
        for filename in os.listdir(package_dir):
            if filename.endswith(".crate"):
                self._build = os.path.join(package_dir, filename)
                break

    def publish(self, registry=None):
        """Publishes the Rust crate using cargo publish."""
        registry = registry or self._registry
        if not self._build:
            raise RuntimeError("Must build before publishing")
        cmd = ["cargo", "publish"]
        if registry:
            cmd.extend(["--registry", registry])
        result = subprocess.run(cmd, cwd=os.path.dirname(self.path), capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Publish failed: {result.stderr}")

    def release(self):
        """Cross-compiles the crate for all supported targets and stages binaries under bin/<arch>/."""
        cargo_dir = os.path.dirname(self.path)
        package_name = self.package

        for target_triple, arch_dir in self.CROSS_TARGETS.items():
            result = subprocess.run(
                ["rustup", "target", "add", target_triple],
                cwd=cargo_dir, capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"rustup target add {target_triple} failed: {result.stderr}")

            result = subprocess.run(
                ["cargo", "build", "--release", "--target", target_triple],
                cwd=cargo_dir, capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"cargo build --target {target_triple} failed: {result.stderr}")

            is_windows = "windows" in target_triple
            binary_name = f"{package_name}.exe" if is_windows else package_name
            src = os.path.join(cargo_dir, "target", target_triple, "release", binary_name)
            dst_dir = os.path.join(cargo_dir, "bin", arch_dir)
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, binary_name)
            shutil.copy2(src, dst)
