"""Tests for the build_and_publish_package python file to confirm that the features of the workflow work as
intended.

These tests are intended to be ran using pytest and use mocked subprocess calls to avoid
actually running build/publish commands.
"""
import os
import tempfile
import shutil
from unittest import mock

import pytest

from vega.packaging import factory
from vega.packaging import const
from vega.packaging.bootstrappers import build_and_publish_package


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
    path = os.path.join(tempfile.tempdir, "test_docker_packaging")
    dockerfile_path = os.path.join(path, "Dockerfile")
    if not os.path.exists(path):
        os.mkdir(path)
        with open(dockerfile_path, "w+") as handle:
            handle.write("FROM python:3.12-slim\n")

    yield path
    if os.path.exists(path):
        shutil.rmtree(path)


# ============================================================================
# Tests for build_and_publish_package.py
# ============================================================================

def test_build_and_publish_no_flags():
    """Test that build_and_publish returns False when neither publish nor release is set."""
    result = build_and_publish_package.build_and_publish([])
    assert result is False


def test_build_and_publish_publish_flag_no_files():
    """Test that build_and_publish returns True with publish=True but no qualifying files."""
    result = build_and_publish_package.build_and_publish([], publish=True)
    assert result is True


def test_build_and_publish_filters_non_build_files(temp_python_project):
    """Test that build_and_publish only processes IS_BUILD_FILE parsers."""
    changelog_path = os.path.join(temp_python_project, "CHANGELOG.md")
    with open(changelog_path, "w") as f:
        f.write("# Changelog\n")

    paths = [changelog_path]
    # changelog is not a build file; should return True but do nothing
    result = build_and_publish_package.build_and_publish(paths, publish=True)
    assert result is True


# ============================================================================
# Tests for PyProject build/publish (mocked subprocess)
# ============================================================================

def test_pyproject_build_success(temp_python_project):
    """Test PyProject.build() calls subprocess correctly within package directory."""
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")
    parser = factory.get_parser_from_path(pyproject_path)

    # Create a fake dist directory with a wheel file
    dist_dir = os.path.join(temp_python_project, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    wheel_path = os.path.join(dist_dir, "test_package-0.1.0-py3-none-any.whl")
    with open(wheel_path, "w") as f:
        f.write("fake wheel")

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        parser.build()

        # Verify subprocess was called without cwd (parser handles it internally)
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["uv", "run", "python", "-m", "build"]
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True

    # Verify _build was set to the wheel path (relative to package directory)
    assert parser._build == os.path.join("dist", "test_package-0.1.0-py3-none-any.whl")


def test_pyproject_build_failure(temp_python_project):
    """Test PyProject.build() raises RuntimeError on failure"""
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")
    parser = factory.get_parser_from_path(pyproject_path)

    mock_result = mock.MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Build error occurred"

    with mock.patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Build failed"):
            parser.build()


def test_pyproject_publish_success(temp_python_project):
    """Test PyProject.publish() calls subprocess correctly"""
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")
    parser = factory.get_parser_from_path(pyproject_path)
    parser._build = "/path/to/package.whl"
    parser._registry = "https://test.pypi.org/legacy/"

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        parser.publish()

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == [
            "uv", "run", "python", "-m", "twine", "upload",
            "--repository-url", "https://test.pypi.org/legacy/",
            "/path/to/package.whl"
        ]


def test_pyproject_publish_without_build(temp_python_project):
    """Test PyProject.publish() raises error if build() wasn't called first"""
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")
    parser = factory.get_parser_from_path(pyproject_path)

    with pytest.raises(RuntimeError, match="Must build before publishing"):
        parser.publish()


def test_pyproject_publish_failure(temp_python_project):
    """Test PyProject.publish() raises RuntimeError on failure"""
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")
    parser = factory.get_parser_from_path(pyproject_path)
    parser._build = "/path/to/package.whl"

    mock_result = mock.MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Upload failed"

    with mock.patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Publish failed"):
            parser.publish()


# ============================================================================
# Tests for ReactPackage build/publish (mocked subprocess)
# ============================================================================

def test_react_package_build_success(temp_react_project):
    """Test ReactPackage.build() calls subprocess correctly within package directory."""
    package_path = os.path.join(temp_react_project, "package.json")
    parser = factory.get_parser_from_path(package_path)

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        parser.build()

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["npm", "run", "build"]
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True

    # Verify _build was set to current directory marker
    assert parser._build == "."


def test_react_package_build_failure(temp_react_project):
    """Test ReactPackage.build() raises RuntimeError on failure"""
    package_path = os.path.join(temp_react_project, "package.json")
    parser = factory.get_parser_from_path(package_path)

    mock_result = mock.MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "npm build error"

    with mock.patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Build failed"):
            parser.build()


def test_react_package_publish_success(temp_react_project):
    """Test ReactPackage.publish() calls subprocess correctly within package directory."""
    package_path = os.path.join(temp_react_project, "package.json")
    parser = factory.get_parser_from_path(package_path)
    parser._registry = "https://npm.pkg.github.com"

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        parser.publish()

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["npm", "publish", "--registry", "https://npm.pkg.github.com"]


def test_react_package_publish_failure(temp_react_project):
    """Test ReactPackage.publish() raises RuntimeError on failure"""
    package_path = os.path.join(temp_react_project, "package.json")
    parser = factory.get_parser_from_path(package_path)

    mock_result = mock.MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "npm publish error"

    with mock.patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Publish failed"):
            parser.publish()


# ============================================================================
# Tests for DockerFile build/publish (mocked subprocess)
# ============================================================================

def test_dockerfile_build_success(temp_docker_project):
    """Test DockerFile.build() calls subprocess correctly"""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    parser = factory.get_parser_from_path(dockerfile_path)

    # Set up registry and version to generate _build path
    parser.registry = "ghcr.io/testuser"
    parser.registry_version = "1.0.0"

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        parser.build()

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "docker"
        assert call_args[0][0][1] == "build"
        assert call_args[0][0][2] == "-t"
        # Build tag should include registry/package:version
        assert "ghcr.io/testuser" in call_args[0][0][3]


def test_dockerfile_build_without_registry(temp_docker_project):
    """Test DockerFile.build() raises error without registry set"""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    parser = factory.get_parser_from_path(dockerfile_path)

    with pytest.raises(RuntimeError, match="Registry must be set"):
        parser.build()


def test_dockerfile_build_failure(temp_docker_project):
    """Test DockerFile.build() raises RuntimeError on failure"""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    parser = factory.get_parser_from_path(dockerfile_path)
    parser.registry = "ghcr.io/testuser"
    parser.registry_version = "1.0.0"

    mock_result = mock.MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "docker build error"

    with mock.patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Docker build failed"):
            parser.build()


def test_dockerfile_publish_success(temp_docker_project):
    """Test DockerFile.publish() calls subprocess correctly"""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    parser = factory.get_parser_from_path(dockerfile_path)
    parser.registry = "ghcr.io/testuser"
    parser.registry_version = "1.0.0"

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        parser.publish()

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "docker"
        assert call_args[0][0][1] == "push"


def test_dockerfile_publish_without_build(temp_docker_project):
    """Test DockerFile.publish() raises error without _build set"""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    parser = factory.get_parser_from_path(dockerfile_path)

    with pytest.raises(RuntimeError, match="Must build before publishing"):
        parser.publish()


def test_dockerfile_publish_failure(temp_docker_project):
    """Test DockerFile.publish() raises RuntimeError on failure"""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    parser = factory.get_parser_from_path(dockerfile_path)
    parser.registry = "ghcr.io/testuser"
    parser.registry_version = "1.0.0"

    mock_result = mock.MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "docker push error"

    with mock.patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Docker push failed"):
            parser.publish()


# ============================================================================
# Tests for parser registry properties
# ============================================================================

def test_pyproject_registry_property(temp_python_project):
    """Test PyProject registry getter and setter"""
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")
    parser = factory.get_parser_from_path(pyproject_path)

    assert parser.registry is None
    parser.registry = "https://test.pypi.org/legacy/"
    assert parser.registry == "https://test.pypi.org/legacy/"


def test_react_package_registry_property(temp_react_project):
    """Test ReactPackage registry getter and setter"""
    package_path = os.path.join(temp_react_project, "package.json")
    parser = factory.get_parser_from_path(package_path)

    assert parser.registry is None
    parser.registry = "https://npm.pkg.github.com"
    assert parser.registry == "https://npm.pkg.github.com"


def test_dockerfile_registry_property(temp_docker_project):
    """Test DockerFile registry getter and setter"""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    parser = factory.get_parser_from_path(dockerfile_path)

    assert parser.registry is None
    parser.registry = "ghcr.io/testuser"
    assert parser.registry == "ghcr.io/testuser"


def test_dockerfile_registry_version_property(temp_docker_project):
    """Test DockerFile registry_version getter and setter"""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    parser = factory.get_parser_from_path(dockerfile_path)

    # registry_version falls back to version (which is None for Dockerfile)
    assert parser.registry_version is None
    parser.registry_version = "2.0.0"
    assert parser.registry_version == "2.0.0"


def test_dockerfile_build_path_generation(temp_docker_project):
    """Test DockerFile generates correct build path from registry and version"""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    parser = factory.get_parser_from_path(dockerfile_path)

    parser.registry = "ghcr.io/myorg"
    parser.registry_version = "1.2.3"

    # _build should be set to registry/package:version
    expected_build = f"ghcr.io/myorg/{parser.package}:1.2.3"
    assert parser._build == expected_build


def test_parser_package_property(temp_python_project, temp_react_project, temp_docker_project):
    """Test package property returns correct package name for each parser type"""
    # PyProject gets name from pyproject.toml
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")
    pyproject_parser = factory.get_parser_from_path(pyproject_path)
    assert pyproject_parser.package == "vega-packaging"

    # ReactPackage gets name from package.json
    package_path = os.path.join(temp_react_project, "package.json")
    react_parser = factory.get_parser_from_path(package_path)
    assert react_parser.package == "test_project"

    # DockerFile gets name from directory name
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")
    docker_parser = factory.get_parser_from_path(dockerfile_path)
    assert docker_parser.package == "test_docker_packaging"


# ============================================================================
# Integration tests for build_and_publish (mocked subprocess)
# ============================================================================

def test_build_and_publish_python_integration(temp_python_project):
    """Integration test: publish=True builds and publishes Python project."""
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")

    dist_dir = os.path.join(temp_python_project, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    wheel_path = os.path.join(dist_dir, "test-0.1.0-py3-none-any.whl")
    with open(wheel_path, "w") as f:
        f.write("fake wheel")

    paths = [pyproject_path]
    repositories = {const.BuildTypes.PYTHON: "https://test.pypi.org/legacy/"}

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        result = build_and_publish_package.build_and_publish(paths, repositories=repositories, publish=True)

        assert result is True
        assert mock_run.call_count == 2


def test_build_and_publish_react_integration(temp_react_project):
    """Integration test: publish=True builds and publishes React project."""
    package_path = os.path.join(temp_react_project, "package.json")

    paths = [package_path]
    repositories = {const.BuildTypes.NPM: "https://npm.pkg.github.com"}

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        result = build_and_publish_package.build_and_publish(paths, repositories=repositories, publish=True)

        assert result is True
        assert mock_run.call_count == 2


def test_build_and_publish_docker_skipped_without_registry(temp_docker_project):
    """Integration test: Docker is skipped without explicit registry."""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")

    paths = [dockerfile_path]

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        result = build_and_publish_package.build_and_publish(paths, publish=True)

        assert result is True
        assert mock_run.call_count == 0


def test_build_and_publish_docker_integration(temp_docker_project):
    """Integration test: Docker is included when explicit registry is provided."""
    dockerfile_path = os.path.join(temp_docker_project, "Dockerfile")

    paths = [dockerfile_path]
    repositories = {const.BuildTypes.DOCKER: "ghcr.io/testuser"}

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        result = build_and_publish_package.build_and_publish(paths, repositories=repositories, publish=True)

        assert result is True
        assert mock_run.call_count == 2


def test_build_and_publish_multiple_types(temp_python_project, temp_react_project):
    """Integration test: publish=True builds + publishes both Python and React projects."""
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")
    package_path = os.path.join(temp_react_project, "package.json")

    dist_dir = os.path.join(temp_python_project, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    wheel_path = os.path.join(dist_dir, "test-0.1.0-py3-none-any.whl")
    with open(wheel_path, "w") as f:
        f.write("fake wheel")

    paths = [pyproject_path, package_path]
    repositories = {
        const.BuildTypes.PYTHON: "https://test.pypi.org/legacy/",
        const.BuildTypes.NPM: "https://npm.pkg.github.com"
    }

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        result = build_and_publish_package.build_and_publish(paths, repositories=repositories, publish=True)

        assert result is True
        assert mock_run.call_count == 4


def test_build_and_publish_release_only(temp_python_project):
    """Integration test: release=True builds and creates a GH release, no publish call."""
    pyproject_path = os.path.join(temp_python_project, "pyproject.toml")

    dist_dir = os.path.join(temp_python_project, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    with open(os.path.join(dist_dir, "test-0.1.0-py3-none-any.whl"), "w") as f:
        f.write("fake wheel")

    paths = [pyproject_path]
    repositories = {const.BuildTypes.PYTHON: "https://test.pypi.org/legacy/"}

    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    mock_result.stdout = "v0.0.0\n"

    with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
        result = build_and_publish_package.build_and_publish(
            paths, repositories=repositories, release=True
        )

        assert result is True
        calls = [c[0][0] for c in mock_run.call_args_list]
        # build called
        assert any(c[0] == "uv" for c in calls)
        # gh release create called
        assert any(c[0] == "gh" for c in calls)
