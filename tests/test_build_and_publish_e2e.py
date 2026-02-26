"""End-to-end tests for the build_and_publish_package workflow.

These tests actually build and publish packages to development registries,
then clean up using REST APIs. They require network access and are marked
with the @pytest.mark.e2e decorator.

Run these tests with:
    uv run pytest tests/test_build_and_publish_e2e.py -v

Skip E2E tests:
    uv run pytest tests/ -v -m "not e2e"
"""
import os
import tempfile
import shutil
import uuid

import pytest
import requests

from vega.packaging import factory
from vega.packaging import const
from vega.packaging.bootstrappers import build_and_publish_package


# Registry URLs
PYPI_DEV_REGISTRY = "https://pypi-dev.vega.style"
DOCKER_DEV_REGISTRY = "registry-dev.vega.style"
PYPI_CLEANUP_API = "https://pypi-cleanup-dev.vega.style"
DOCKER_CLEANUP_API = "https://registry-cleanup-dev.vega.style"


# ============================================================================
# Helper Functions
# ============================================================================

def cleanup_pypi_package(package_name: str) -> bool:
    """Delete a package from the PyPI dev registry.

    Args:
        package_name: Name of the package to delete

    Returns:
        True if cleanup was successful or package didn't exist
    """
    response = requests.delete(f"{PYPI_CLEANUP_API}/package/{package_name}")
    return response.status_code in (200, 404)


def cleanup_docker_image(image_name: str) -> bool:
    """Delete an image from the Docker dev registry.

    Args:
        image_name: Name of the image to delete (e.g., 'test/vega-test-package')

    Returns:
        True if cleanup was successful or image didn't exist
    """
    response = requests.delete(f"{DOCKER_CLEANUP_API}/package/{image_name}")
    return response.status_code in (200, 404)


def generate_test_package_name() -> str:
    """Generate unique package name for test isolation.

    Returns:
        A unique package name like 'vega-test-a1b2c3d4'
    """
    return f"vega-test-{uuid.uuid4().hex[:8]}"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def e2e_python_project():
    """Create a minimal publishable Python package with unique name.

    Yields:
        Tuple of (project_path, package_name)

    Cleanup:
        Removes package from registry and deletes local files
    """
    package_name = generate_test_package_name()
    path = os.path.join(tempfile.tempdir, package_name)
    os.makedirs(path, exist_ok=True)

    # Create pyproject.toml
    with open(os.path.join(path, "pyproject.toml"), "w") as f:
        f.write(f"""[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{package_name}"
version = "0.0.1"
description = "Test package for E2E testing"
""")

    # Create minimal package structure
    pkg_dir = os.path.join(path, package_name.replace("-", "_"))
    os.makedirs(pkg_dir, exist_ok=True)
    with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
        f.write('__version__ = "0.0.1"\n')

    yield path, package_name

    # Cleanup: remove from registry and local filesystem
    cleanup_pypi_package(package_name)
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def e2e_docker_project():
    """Create a minimal Docker project with unique image name.

    Yields:
        Tuple of (project_path, image_name)

    Cleanup:
        Removes image from registry and deletes local files
    """
    image_name = f"test/{generate_test_package_name()}"
    path = os.path.join(tempfile.tempdir, "docker_e2e_test")
    os.makedirs(path, exist_ok=True)

    # Create minimal Dockerfile
    with open(os.path.join(path, "Dockerfile"), "w") as f:
        f.write("FROM alpine:latest\nCMD [\"echo\", \"test\"]\n")

    yield path, image_name

    # Cleanup: remove from registry and local filesystem
    cleanup_docker_image(image_name)
    shutil.rmtree(path, ignore_errors=True)


# ============================================================================
# End-to-End Tests
# ============================================================================

@pytest.mark.e2e
def test_python_build_and_publish_e2e(e2e_python_project):
    """E2E: Build and publish Python package to dev registry, then cleanup."""
    project_path, package_name = e2e_python_project
    pyproject_path = os.path.join(project_path, "pyproject.toml")

    parser = factory.get_parser_from_path(pyproject_path)
    parser.registry = PYPI_DEV_REGISTRY

    # Build
    parser.build()
    assert parser._build is not None
    assert parser._build.endswith(".whl")

    # Publish
    parser.publish()

    # Cleanup handled by fixture


@pytest.mark.e2e
def test_docker_build_and_publish_e2e(e2e_docker_project):
    """E2E: Build and push Docker image to dev registry, then cleanup."""
    project_path, image_name = e2e_docker_project
    dockerfile_path = os.path.join(project_path, "Dockerfile")

    parser = factory.get_parser_from_path(dockerfile_path)
    parser.registry = DOCKER_DEV_REGISTRY
    parser.registry_version = "0.0.1"

    # Build
    parser.build()
    assert parser._build is not None

    # Publish
    parser.publish()

    # Cleanup handled by fixture


@pytest.mark.e2e
def test_build_and_publish_function_e2e(e2e_python_project):
    """E2E: Test full build_and_publish() function with real registry."""
    project_path, package_name = e2e_python_project
    pyproject_path = os.path.join(project_path, "pyproject.toml")

    message_str = "#minor #added E2E test package"
    paths = [pyproject_path]
    repositories = {const.BuildTypes.PYTHON: PYPI_DEV_REGISTRY}

    result = build_and_publish_package.build_and_publish(message_str, paths, repositories)
    assert result is True

    # Cleanup handled by fixture
