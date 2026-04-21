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
import argparse
from unittest import mock

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


@pytest.fixture
def temp_docker_project():
    """Temporary docker project directory for testing."""
    path = os.path.join(tempfile.tempdir, "test_docker_semver_packaging")
    dockerfile_path = os.path.join(path, "Dockerfile")
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)
    with open(dockerfile_path, "w+") as handle:
        handle.write("FROM python:3.12-slim\n")

    yield path
    if os.path.exists(path):
        shutil.rmtree(path)


@pytest.fixture
def temp_changelog_only_project():
    """Temporary project directory containing only an autocreated changelog."""
    path = os.path.join(tempfile.tempdir, "test_changelog_only_packaging")
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)

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


def test_parser_priorities():
    """Version resolution should prefer code files first, then Docker, then changelog."""
    pyproject_cls = factory.get_parser_cls_by_filename("pyproject.toml")
    react_cls = factory.get_parser_cls_by_filename("package.json")
    cargo_cls = factory.get_parser_cls_by_filename("Cargo.toml")
    docker_cls = factory.get_parser_cls_by_filename("Dockerfile")
    changelog_cls = factory.get_parser_cls_by_filename("CHANGELOG.md")

    assert pyproject_cls.PRIORITY == 1
    assert react_cls.PRIORITY == 1
    assert cargo_cls.PRIORITY == 1
    assert docker_cls.PRIORITY == 2
    assert changelog_cls.PRIORITY == 3


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

    # DockerFile resolves its version dynamically from image tags and falls back to 0.0.0
    assert dockerfile_parser.version == "0.0.0"
    assert dockerfile_parser.HAS_VERSION is False
    assert dockerfile_parser.IS_BUILD_FILE is True
    assert dockerfile_parser.BUILD_TYPE == const.BuildTypes.DOCKER

    # update() is a no-op for Docker metadata
    message = commits.CommitMessage("#major #added added dockerfile support")
    assert dockerfile_parser.update(message, None) is None


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
    githubenv_parser.builds = ["python", "docker"]
    githubenv_parser.update(message, None)

    with open(githubenv_parser.path, "r") as handle:
        content = handle.read()
        assert re.search("SEMANTIC_VERSION=1.0.0", content) is not None
        assert re.search("BUILD=python:docker", content) is not None
        assert re.search("PUBLISH=False", content) is not None
        assert re.search("RELEASE=False", content) is not None


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

    # Check CHANGELOG.md
    changelog_path = os.path.join(temp_python_project, "CHANGELOG.md")
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

    # Check CHANGELOG.md
    changelog_path = os.path.join(temp_react_project, "CHANGELOG.md")
    changelog_cls = factory.get_parser_cls_by_filename("changelog.md")

    content = f"{changelog_cls.TEMPLATE}\n{message.markdown('0.1.0')}"
    with open(changelog_path, "r") as handle:
        assert handle.read() == content

    # Check pyproject.toml
    pyproject_path = os.path.join(temp_react_project, "package.json")

    with open(pyproject_path, "r") as handle:
        assert json.load(handle)["version"] == "0.1.0"


def test_update_semantic_version_changelog_only(temp_changelog_only_project):
    """Integration test for autocreating and updating a standalone changelog."""
    message_str = "#patch #fixed fixed changelog-only workflow"
    changelog_path = os.path.join(temp_changelog_only_project, "CHANGELOG.md")

    update_semantic_version.update_semantic_version(message_str, [changelog_path])

    message = commits.CommitMessage(message_str)
    changelog_cls = factory.get_parser_cls_by_filename("changelog.md")

    content = f"{changelog_cls.TEMPLATE}\n{message.markdown('0.0.1')}"
    with open(changelog_path, "r") as handle:
        assert handle.read() == content


def test_update_semantic_version_docker_only_uses_registry_version(temp_docker_project):
    """Docker-only version matching should use the Docker image version instead of changelog fallback."""
    message_str = "#patch #fixed fixed docker-only workflow"
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    changelog_path = os.path.join(temp_docker_project, "CHANGELOG.md")

    parsers = update_semantic_version.get_parsers_dict([dockerfile_path, changelog_path])
    docker_cls = parsers["builds"][const.BuildTypes.DOCKER][0].__class__

    with mock.patch.object(docker_cls, "_DockerFile__get_image_tags", return_value=["1.2.3", "latest"]), \
         mock.patch.object(docker_cls, "_DockerFile__get_git_repository", return_value=None):
        for docker_parser in parsers["builds"][const.BuildTypes.DOCKER]:
            docker_parser.registry = "ghcr.io/testuser"

        update_semantic_version.update_semantic_version(message_str, parsers=parsers)

    with open(changelog_path, "r") as handle:
        content = handle.read()
    assert "## [1.2.4]" in content
    assert "- fixed docker-only workflow" in content


def test_update_semantic_version_main_applies_docker_registry(temp_docker_project, monkeypatch):
    """main() should set the explicit Docker registry before resolving Docker image versions."""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    changelog_path = os.path.join(temp_docker_project, "CHANGELOG.md")

    args = argparse.Namespace(
        subject="#minor #added added docker registry support",
        description=None,
        directory=temp_docker_project,
        changelog_path=changelog_path,
        pyproject_path=None,
        react_package_path=None,
        dockerfile_path=dockerfile_path,
        docker_registry="ghcr.io/testuser",
        cargo_path=None,
        github_env=False,
        verbose=False,
        log_to_disk=False,
    )

    parsers = update_semantic_version.get_parsers_dict([dockerfile_path, changelog_path])
    docker_cls = parsers["builds"][const.BuildTypes.DOCKER][0].__class__

    def fake_get_image_tags(self):
        assert self.registry == "ghcr.io/testuser"
        return ["2.3.4"]

    monkeypatch.setattr(update_semantic_version, "parse_args", lambda: args)
    monkeypatch.setattr(update_semantic_version, "get_parsers_dict", lambda paths: parsers)
    monkeypatch.setattr(update_semantic_version.log, "setup", lambda *args, **kwargs: None)

    with mock.patch.object(docker_cls, "_DockerFile__get_image_tags", fake_get_image_tags), \
         mock.patch.object(docker_cls, "_DockerFile__get_git_repository", return_value=None):
        update_semantic_version.main()

    with open(changelog_path, "r") as handle:
        content = handle.read()
    assert "## [2.4.0]" in content
    assert "- added docker registry support" in content


def test_update_semantic_version_main_sets_github_env_builds(temp_python_project, temp_docker_project, githubenv_path, monkeypatch):
    """main() should populate BUILD/PUBLISH/RELEASE in GITHUB_ENV from discovered build files."""
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    with open(githubenv_path, "w") as handle:
        handle.write("")

    args = argparse.Namespace(
        subject="#minor #publish #release added build env support",
        description=None,
        directory=temp_python_project,
        changelog_path=None,
        pyproject_path=pyproject_path,
        react_package_path=None,
        dockerfile_path=dockerfile_path,
        docker_registry="ghcr.io/testuser",
        cargo_path=None,
        github_env=True,
        verbose=False,
        log_to_disk=False,
    )

    monkeypatch.setattr(update_semantic_version, "parse_args", lambda: args)
    monkeypatch.setattr(update_semantic_version.log, "setup", lambda *args, **kwargs: None)
    monkeypatch.setenv("GITHUB_ENV", githubenv_path)

    with mock.patch("vega.packaging.io.yield_paths", return_value=[pyproject_path, dockerfile_path, githubenv_path]), \
         mock.patch("vega.packaging.parsers.docker.DockerFile._DockerFile__get_image_tags", return_value=[]), \
         mock.patch("vega.packaging.parsers.docker.DockerFile._DockerFile__get_git_repository", return_value=None):
        update_semantic_version.main()

    with open(githubenv_path, "r") as handle:
        content = handle.read()
    assert "SEMANTIC_VERSION=0.1.0" in content
    assert "BUILD=python:docker" in content
    assert "PUBLISH=True" in content
    assert "RELEASE=True" in content


# ============================================================================
# Tests for Cargo parser
# ============================================================================

@pytest.fixture
def temp_cargo_project():
    """Temporary Cargo project directory for testing."""
    path = os.path.join(tempfile.tempdir, "test_cargo_packaging")
    cargo_path = os.path.join(path, "Cargo.toml")
    if not os.path.exists(path):
        os.mkdir(path)
        with open(cargo_path, "w+") as handle:
            handle.write('[package]\nname = "test_crate"\nversion = "0.0.0"\nedition = "2021"\n')
    yield path
    if os.path.exists(path):
        shutil.rmtree(path)


def test_cargo_parser_update(temp_cargo_project):
    """Test that Cargo.update() bumps the version under [package]."""
    from unittest import mock
    cargo_path = os.path.join(temp_cargo_project, "Cargo.toml")
    parser = factory.get_parser_from_path(cargo_path)

    message = commits.CommitMessage("#minor #added added a feature")
    parser.update(message, None)

    with open(cargo_path, "r") as handle:
        content = toml.load(handle)
    assert content["package"]["version"] == "0.1.0"


def test_cargo_build_success(temp_cargo_project):
    """Test Cargo.build() calls cargo package and sets _build to .crate path."""
    from unittest import mock
    cargo_path = os.path.join(temp_cargo_project, "Cargo.toml")
    parser = factory.get_parser_from_path(cargo_path)

    package_dir = os.path.join(temp_cargo_project, "target", "package")
    os.makedirs(package_dir, exist_ok=True)
    crate_path = os.path.join(package_dir, "test_crate-0.0.0.crate")
    with open(crate_path, "w") as f:
        f.write("fake crate")

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        parser.build()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["cargo", "package"]

    assert parser._build.endswith(".crate")


def test_cargo_publish_success(temp_cargo_project):
    """Test Cargo.publish() calls cargo publish without --registry when none set."""
    from unittest import mock
    cargo_path = os.path.join(temp_cargo_project, "Cargo.toml")
    parser = factory.get_parser_from_path(cargo_path)
    parser._build = "/fake/path/test_crate-0.0.0.crate"

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        parser.publish()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["cargo", "publish"]


def test_cargo_publish_with_registry(temp_cargo_project):
    """Test Cargo.publish() includes --registry when a registry is set."""
    from unittest import mock
    cargo_path = os.path.join(temp_cargo_project, "Cargo.toml")
    parser = factory.get_parser_from_path(cargo_path)
    parser._build = "/fake/path/test_crate-0.0.0.crate"
    parser._registry = "my-registry"

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        parser.publish()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["cargo", "publish", "--registry", "my-registry"]


def test_cargo_publish_without_build(temp_cargo_project):
    """Test Cargo.publish() raises error if build() wasn't called first."""
    cargo_path = os.path.join(temp_cargo_project, "Cargo.toml")
    parser = factory.get_parser_from_path(cargo_path)
    import pytest
    with pytest.raises(RuntimeError, match="Must build before publishing"):
        parser.publish()


# ============================================================================
# Tests for #publish / #release commit keywords
# ============================================================================

def test_commit_publish_keyword():
    """#publish sets publish=True, release=False."""
    message = commits.CommitMessage("#minor #publish add new feature")
    assert message.publish is True
    assert message.release is False


def test_commit_release_keyword():
    """#release sets release=True, publish=False."""
    message = commits.CommitMessage("#minor #release add new feature")
    assert message.publish is False
    assert message.release is True


def test_commit_publish_and_release_keywords():
    """#publish #release sets both to True."""
    message = commits.CommitMessage("#minor #publish #release add new feature")
    assert message.publish is True
    assert message.release is True


def test_commit_no_workflow_keywords():
    """No workflow keyword leaves both False."""
    message = commits.CommitMessage("#minor #added add new feature")
    assert message.publish is False
    assert message.release is False


# ============================================================================
# Tests for changelog.changes()
# ============================================================================

MULTI_VERSION_CHANGELOG = """\
# Changelog

## [1.1.0] - 2024/01/01
### Added
- feature two

## [1.0.0] - 2023/01/01
### Added
- feature one

## [0.1.0] - 2022/01/01
### Added
- initial release
"""


@pytest.fixture
def multi_version_changelog(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    path.write_text(MULTI_VERSION_CHANGELOG)
    return str(path)


def test_changes_latest(multi_version_changelog):
    """changes() with no args returns the latest versioned section."""
    parser = factory.get_parser_from_path(multi_version_changelog)
    result = parser.changes()
    assert result.startswith("## [1.1.0]")
    assert "## [1.0.0]" not in result


def test_changes_specific_version(multi_version_changelog):
    """changes("1.0.0") returns just that section."""
    parser = factory.get_parser_from_path(multi_version_changelog)
    result = parser.changes("1.0.0")
    assert result.startswith("## [1.0.0]")
    assert "## [1.1.0]" not in result
    assert "## [0.1.0]" not in result


def test_changes_version_range(multi_version_changelog):
    """changes("1.1.0", "0.1.0") returns sections from 1.1.0 down to (not including) 0.1.0."""
    parser = factory.get_parser_from_path(multi_version_changelog)
    result = parser.changes("1.1.0", "0.1.0")
    assert "## [1.1.0]" in result
    assert "## [1.0.0]" in result
    assert "## [0.1.0]" not in result


def test_changes_missing_version(multi_version_changelog):
    """changes() for a version that doesn't exist returns empty string."""
    parser = factory.get_parser_from_path(multi_version_changelog)
    result = parser.changes("9.9.9")
    assert result == ""
