"""Python script for building and publishing packages to their respective repositories.

This supports any file that has had a parser made for it.
"""
import os
import argparse

from vega.packaging import const
from vega.packaging import factory
from vega.packaging import io
from vega.packaging import log
from vega.packaging import platforms
from vega.packaging.parsers.changelog import Changelog

logger = log.get(__name__)


def parse_args():
    """Parse command-line arguments for the build and publish script.

    Returns:
        argparse.Namespace: Parsed arguments with all user-provided options.

    Raises:
        SystemExit: If argument parsing fails or --help is requested.
    """
    parser = argparse.ArgumentParser(
        prog='Build and Publish',
        description='Builds and publishes the packages to their respective repositories',
    )
    parser.add_argument("-d", "--directory", help="directory to look for files to update", default=os.getcwd())
    parser.add_argument("-p", "--pypi_registry", help="registry to publish python package to")
    parser.add_argument("-n", "--npm_registry", help="registry to publish npm packages to")
    parser.add_argument("-r", "--docker_registry", help="registry to publish docker images to")
    parser.add_argument("-c", "--cargo_registry", help="named crates.io registry (optional)")
    parser.add_argument("-pp", "--pyproject_path", help="path to the pyproject.toml file")
    parser.add_argument("-pb", "--publish", help="publish packages to their registries",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-rl", "--release", help="create a release on the given platform; omit to skip, pass without a value to default to github, or pass a provider name (e.g. --release gitlab)",
                        nargs="?", const="github", default=None)
    parser.add_argument("-co", "--compile_only", help="build cross-platform release artifacts without creating a release",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-v", "--verbose", help="print out debug statements",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-l", "--log_to_disk", help="saves out logs to disk",
                        action=argparse.BooleanOptionalAction)
    return parser.parse_args()


def build_and_publish(
    paths: list[str],
    repositories: dict | None = None,
    publish: bool = False,
    release: bool = False,
    release_provider: str = "github",
    compile_only: bool = False,
) -> bool:
    """Build and optionally publish or release packages.

    Scans the provided paths for supported package files (pyproject.toml,
    package.json, Cargo.toml, Dockerfile), builds them, and optionally
    publishes to registries or creates GitHub/GitLab releases.

    Build and publish operations for each package are executed within the
    package's directory to ensure proper tool behavior.

    Args:
        paths: File paths to scan for buildable packages.
        repositories: Mapping of BuildTypes to registry URLs/names.
            Example: {BuildTypes.PYTHON: "https://pypi.org/simple"}
        publish: Whether to publish packages after building.
        release: Whether to create a release on the release provider.
        release_provider: Name of the release provider (e.g., "github", "gitlab").
        compile_only: Whether to build release artifacts without creating a release.

    Returns:
        True if any operation was performed, False if no action was requested
        or no packages were found.
    """
    if not publish and not release and not compile_only:
        return False

    repositories = repositories or {}

    packaging_files = []
    for path in paths:
        file_parser = factory.get_parser_from_path(path)
        if not file_parser or not file_parser.IS_BUILD_FILE:
            continue
        registry = repositories.get(file_parser.BUILD_TYPE) or getattr(file_parser, "DEFAULT_REGISTRY", None)
        if registry is None and file_parser.BUILD_TYPE != const.BuildTypes.RUST:
            continue
        file_parser.registry = registry
        packaging_files.append(file_parser)

    packaging_files.sort(key=lambda file_parser: file_parser.PRIORITY)

    if compile_only:
        for file_parser in packaging_files:
            if file_parser.RELEASE_PATH is not None:
                logger.info(f"Compiling release artifacts for {file_parser.path}")
                file_parser.release()
        return True

    for file_parser in packaging_files:
        logger.info(f"Building {file_parser.path}")
        file_parser.build()

    if publish:
        for file_parser in packaging_files:
            logger.info(f"Publishing {file_parser.path}")
            file_parser.publish()

    if release:
        cwd = os.path.dirname(packaging_files[0].path) if packaging_files else os.getcwd()
        release_platform = platforms.get(release_provider, cwd)
        since = release_platform.last_release

        changelog = None
        for path in paths:
            file_parser = factory.get_parser_from_path(path)
            if file_parser and isinstance(file_parser, Changelog):
                changelog = file_parser
                break

        notes = changelog.changes(since=since) if changelog else ""
        version = str(packaging_files[0].version) if packaging_files else (str(changelog.version) if changelog else "")

        release_files = []
        for file_parser in packaging_files:
            if file_parser.RELEASE_PATH is not None:
                release_dir = os.path.join(os.path.dirname(file_parser.path), file_parser.RELEASE_PATH)
                if os.path.isdir(release_dir):
                    for dirpath, _, filenames in os.walk(release_dir):
                        for filename in filenames:
                            release_files.append(os.path.join(dirpath, filename))

        release_platform.create(version, notes, files=release_files or None)

    return True


def main() -> None:
    """Execute the build and publish workflow from command-line arguments.

    Parses arguments, discovers packages in the specified directory,
    and delegates to build_and_publish() to perform the requested operations.

    Example:
        $ python build_and_publish_package.py -d ./projects --publish
    """
    args = parse_args()

    log.setup("build_and_publish", verbose=args.verbose, write_to_disk=args.log_to_disk)

    repositories = {}
    if args.pypi_registry:
        repositories[const.BuildTypes.PYTHON] = args.pypi_registry
    if args.npm_registry:
        repositories[const.BuildTypes.NPM] = args.npm_registry
    if args.docker_registry:
        repositories[const.BuildTypes.DOCKER] = args.docker_registry
    if args.cargo_registry:
        repositories[const.BuildTypes.RUST] = args.cargo_registry

    explicit_paths = [args.pyproject_path]
    filepath_generator = io.yield_paths(args.directory, explicit_paths)

    build_and_publish(
        list(filepath_generator),
        repositories=repositories,
        publish=args.publish or False,
        release=args.release is not None,
        release_provider=args.release or "github",
        compile_only=args.compile_only or False,
    )


if __name__ == "__main__":
    main()
