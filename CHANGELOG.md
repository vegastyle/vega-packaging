# Changelog

All notable changes to the project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


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

