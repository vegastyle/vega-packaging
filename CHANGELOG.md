# Changelog

All notable changes to the project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [0.7.1] - 2026/04/18 07:51:34

### Changed

- versioning-workflow to version 1.4.1

### Fixed

- BUILD env var from being built with the enum object and to use the enum values instead.


## [0.7.0] - 2026/04/18 03:16:33

### Added

- support for updating the version of a docker-compose.yaml version
- refactored logic for parsing files to also support building and publishing workflows per file type plugin
- support for docker files
- versions file for holding class object that handles versioning logic
- tests to confirm build and publish behaviour works
- cross-platform Rust release support with compile_only flag and per-language reusable workflows
- RELEASE_PATH and CROSS_TARGETS to Cargo parser
- --compile_only flag to build_and_publish CLI
- file attachment support to Github.create()
- build_and_publish_rust build_and_publish_python build_and_publish_react build_and_publish_docker reusable workflows
- bump_build_and_publish.yml top-level orchestration workflow
- context manager for working directory handling

### Changed

- decoupled consts and resuable functions to their own modules
- semantic versioning tests to work with new refactored code
- update_version_workflow.yml to remove build-and-publish job and expose build type outputs
- README.md and example/README.md to document all new capabilities
- parsers to set the current working directory to where the package files live
- short name cli parameter flags to be consistent with the different languages
- docstrings and variable names
- readme with examples on how to add build, publish, and release steps to the parsers


## [0.6.2] - 2025/04/21 16:46:21

### Fixed

- replaced args.message with message in the update_semantic_version.py file


## [0.6.1] - 2025/04/21 16:35:15

### Fixed

- added break to ensure the loop stops if the subject has a hashtag


## [0.6.0] - 2025/04/21 16:27:13

### Added

- subject and body arguments to support reading boths portions of a message, with the description being prioritized for parsing when provided


## [0.5.1] - 2025/04/15 16:33:06

### Added

- test to check that a react project version is updated properly.


## [0.5.0] - 2025/04/08 17:17:08

### Added

- support for bumping up the semantic version of package.json files from React projects.

### Changed

- added unit test for confirming that the semantic version for react packages updates properly.
- update_semantic_version.py now supports a react_package_path flag for specifying the react package file to update.


## [0.4.1] - 2024/07/24 01:43:01

### Added

- added -log_to_disk flag to write logs to disk.


## [0.4.0] - 2024/07/24 01:15:12

### Added

- added verbose flag to make the command more verbose

### Changed

- added logging support


## [0.3.3] - 2024/07/10 22:37:47

### Fixed

- fixed typo in the name of the on_push.yml workflow


## [0.3.2] - 2024/07/08 07:51:00

### Added

- adding required permissions to on_push.yml workflow file


## [0.3.1] - 2024/07/08 03:32:22

### Fixed

- fixed bug where files where getting parsed twice if a relative path was used when explicitly setting which files to 
parse via the --changelog_path and --pyproject_path flags. 


## [0.3.0] - 2024/07/08 02:54:41

### Added

- added insert_version_index property to changelog.md to ensure that the insert index is always resolved.


## [0.2.0] - 2024/07/07 04:52:00

### Added

- Added support for the GitHub env file
- Added support for setting priority to the file parsers plugin to dictate parsing order
- Added more content to the READEME.md with instructions on how to install and use this package
- Added additional unit and integration tests to confirm everything works
- Added reset method to the parsers class to reset the internal values so the data can be parsed again internally. 

## [0.1.0] - 2024/07/05 11:02:39

### Added

- Initial release of the vega-package package
- Includes update_semantic_version cli command

