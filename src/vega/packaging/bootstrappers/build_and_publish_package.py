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
    """Parses the arguments passed to this module"""
    parser = argparse.ArgumentParser(
        prog='Build and Publish',
        description='Builds and publishes the packages to their respective repositories',
    )
    parser.add_argument("-d", "--directory", help="directory to look for files to update", default=os.getcwd())
    parser.add_argument("-p", "--pypi_registry", help="registry to publish python package to")
    parser.add_argument("-n", "--npm_registry", help="registry to publish npm packages to")
    parser.add_argument("-r", "--docker_registry", help="registry to publish docker images to")
    parser.add_argument("--cargo_path", help="path to the Cargo.toml file")
    parser.add_argument("--cargo_registry", help="named crates.io registry (optional)")
    parser.add_argument("--pyproject_path", help="path to the pyproject.toml file")
    parser.add_argument("--publish", help="publish packages to their registries",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--release", help="create a release on the release provider",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--compile_only", help="build cross-platform release artifacts without creating a release",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--release_provider", help="release provider to use", default="github")
    parser.add_argument("-v", "--verbose", help="print out debug statements",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("-l", "--log_to_disk", help="saves out logs to disk",
                        action=argparse.BooleanOptionalAction)
    return parser.parse_args()


def build_and_publish(paths: list[str], repositories=None, publish=False,
                      release=False, release_provider="github", compile_only=False):
    """Builds and optionally publishes/releases packages found in the given paths.

    Args:
        paths: list of file paths to scan for buildable packages.
        repositories: dict mapping BuildTypes to registry URLs/names.
        publish: if True, publish packages after building.
        release: if True, create a release on the release provider.
        release_provider: name of the release provider (e.g. "github").
        compile_only: if True, cross-compile release binaries without creating a release.
    """
    if not publish and not release and not compile_only:
        return False

    repositories = repositories or {}

    packaging_files = []
    for path in paths:
        pf = factory.get_parser_from_path(path)
        if not pf or not pf.IS_BUILD_FILE:
            continue
        registry = repositories.get(pf.BUILD_TYPE) or getattr(pf, "DEFAULT_REGISTRY", None)
        if registry is None and pf.BUILD_TYPE != const.BuildTypes.RUST:
            continue
        pf.registry = registry
        packaging_files.append(pf)

    packaging_files.sort(key=lambda pf: pf.PRIORITY)

    if compile_only:
        for pf in packaging_files:
            if pf.RELEASE_PATH is not None:
                logger.info(f"Compiling release artifacts for {pf.path}")
                pf.release()
        return True

    for pf in packaging_files:
        logger.info(f"Building {pf.path}")
        pf.build()

    if publish:
        for pf in packaging_files:
            logger.info(f"Publishing {pf.path}")
            pf.publish()

    if release:
        cwd = os.path.dirname(packaging_files[0].path) if packaging_files else os.getcwd()
        platform = platforms.get(release_provider, cwd)
        since = platform.last_release

        changelog = None
        for path in paths:
            pf = factory.get_parser_from_path(path)
            if pf and isinstance(pf, Changelog):
                changelog = pf
                break

        notes = changelog.changes(since=since) if changelog else ""
        version = str(packaging_files[0].version) if packaging_files else (str(changelog.version) if changelog else "")

        release_files = []
        for pf in packaging_files:
            if pf.RELEASE_PATH is not None:
                release_dir = os.path.join(os.path.dirname(pf.path), pf.RELEASE_PATH)
                if os.path.isdir(release_dir):
                    for dirpath, _, filenames in os.walk(release_dir):
                        for filename in filenames:
                            release_files.append(os.path.join(dirpath, filename))

        platform.create(version, notes, files=release_files or None)

    return True


def main():
    """Main function to call in this bootstrapper"""
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

    explicit_paths = [args.pyproject_path, args.cargo_path]
    filepath_generator = io.yield_paths(args.directory, explicit_paths)

    build_and_publish(
        list(filepath_generator),
        repositories=repositories,
        publish=args.publish or False,
        release=args.release or False,
        release_provider=args.release_provider or "github",
        compile_only=args.compile_only or False,
    )


if __name__ == "__main__":
    main()
