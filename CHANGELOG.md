# Changelog

All notable changes to the project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


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

