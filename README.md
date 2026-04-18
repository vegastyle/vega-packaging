# vega-packaging
> Python package for creating and editing files required for packaging code based on commit messages.

This python package contains utility code relating to packaging workflows such as versioning, creating required files 
from templates, testing builds, etc. based on the commit messages when that code was updated.

---
## Supported Build Types

| Type   | File          | Description                                                        |
|--------|---------------|--------------------------------------------------------------------|
| Python | pyproject.toml | Builds and publishes Python packages to PyPI or a private registry |
| NPM    | package.json  | Builds and publishes NPM packages to a registry                    |
| Docker | Dockerfile    | Builds and pushes Docker images to a container registry            |
| Rust   | Cargo.toml    | Packages/publishes Rust crates and cross-compiles release binaries |

---
## How to install
```commandline
pip install git+https://github.com/vegastyle/vega-packaging.git
```
---
## Working with Commit Messages

The commits library supports reading commit messages parsing their hashtags to get information about the commit. 

### Example
```python
""" You can check the commit messages, as well as set the semantic version that is supposed to be associated with it"""
from vega.packaging import commits

# Parsing a string from a version control system that uses hashtags to indicate the changes that were submitted
message_str = "#patch #added added good vibes #removed removed bad vibes #fixed fixed the vibes #fixed also fixed a bug"
commit_message = commits.CommitMessage(message_str)

# Get the version number to bump
# The Versions Enums are used from the commits module
# The supported enums are MAJOR, MINOR, and PATCH
print(commit_message.bump) # commits.Versions.PATCH

# Get the list of the changes included in the commit message
# The Changes Enums are used from the commits module
# The supported enums are ADDED, REMOVED, CHANGED, UPDATED, FIXED, SECURITY 
print(commit_message.changes[commits.Changes.ADDED]) # ["added good vibes"]
print(commit_message.changes[commits.Changes.REMOVED]) # ["removed bad vibes"]
print(commit_message.changes[commits.Changes.FIXED]) # ["fixed the vibes", "also fixed the bug"]

# By design, the message doesn't know the version number as it is usually obtained through other files.
# As such you can set the semantic version and perform the following operations

commit_message.semantic_version = "0.1.0"
# prints a changelog markdown based on the message
print(commit_message.markdown) 

# Update the semantic version,  this consumes the value of bump and sets it to None
commit_message.bump_semantic_version()
print(commit_message.semantic_version) # "0.1.1"

```
---
## build_and_publish CLI
Installing this package provides access to the **build_and_publish** cli command.
This command builds, publishes, and/or creates a release for packages found in the current directory.

### Basic Usage
```commandline
build_and_publish --publish --release
```

#### Key Flags
* **--publish** — Build and publish packages to their registries (PyPI, npm, crates.io, Docker registry).
* **--release** — Create a GitHub release, attaching any staged release artifacts (e.g. cross-compiled binaries).
* **--compile_only** — Cross-compile Rust release binaries and stage them under `bin/<arch>/` without creating a release.
  Combine with `--publish` to publish to crates.io at the same time:
  ```commandline
  build_and_publish --publish --compile_only
  ```
* **--release_provider** — Release provider to use. Currently supports `github` (default).
* **--cargo_path** — Explicit path to a `Cargo.toml` file.
* **--pypi_registry** / **--npm_registry** / **--docker_registry** / **--cargo_registry** — Registry overrides for each build type.

---
## update_semantic_version CLI
Installing this package provides access to the **update_semantic_version** cli command. 
This command updates the semantic version in various files of a directory. 

This command was written with the intention of being used in a CI/CD workflow to automate updating the semantic verison 
in various files at once based on a commit message. 

### Basic Usage
```commandline
update_semantic_version --message "#patch #added good vibes"
```

By default the command will search the current directory for files that it supports and will bump up the semantic version
of those files.

Supported files are parsed in order of priority, with 1 being the highest priority number.

#### Supported Arguments
* **--message**
    * Required Argument.
    * The message to parse to use for bumping the version number and to add to the changelog file.<br><br>This is uses the CommitMessage class and supports the following hashtags:<br><br>
      * Versions to bum<br>(accepts only one per message)
        * #major
        * #minor
        * #patch<br><br>
      * Changes to log<br>(supports multiple in a message)
        * #added
        * #removed
        * #changed
        * #updated
        * #fixed
        * #security
      * Trigger build related jobs
        * #publish
          * Build and publish the built code to a public or private registry
        * #release
          * Build and release the the built code and executables through a release provider. Currently only GitHub is supported.  
      * Ignore this commmit from CI/CD workflows
        * #ignore

* **--directory**
  * Optional Argument
  * Directory to search for files to update.
    * Defaults to the current working directory.<br><br>
* **--changelog_path**
  * Optional Argument
  * Path to the CHANGELOG.md file to update. It creates one if it doesn't exist.<br><br>
* **--pyproject_path**
  * Optional Argument: 
  * Path to the pyproject.toml file to update. It doesn't create one if it doesn't exist.<br><br>
* **--cargo_path**
  * Optional Argument
  * Path to the `Cargo.toml` file to update.<br><br>
* **--github_env**
  * Optional Flag
  * When set, it looks for the GitHub env file from the `GITHUB_ENV` environment variable and:
    * Sets `SEMANTIC_VERSION` to the new semantic version.
    * Sets `PUBLISH` and `RELEASE` flags based on the commit hashtags.
    * Sets `BUILD_RUST=True`, `BUILD_PYTHON=True`, `BUILD_NPM=True`, and/or `BUILD_DOCKER=True` for each build file type found in the directory.

#### Supported Files
The following files are supported and their parsing priority (1 = highest):
* **pyproject.toml** — Priority: 1
* **Cargo.toml** — Priority: 1
* **CHANGELOG.md** — Priority: 2
* **package.json** — Priority: 3
* **Dockerfile** — Priority: 4
* **GitHub env file** — Priority: 5
  * GitHub Env files follow the naming convention of `set_env_*` where the asterisk is a unique identifier for the workflow session.
    * Example filename: `set_env_86bd2d54-09b3-476f-8235-5936444c37fa`
    
---
## Adding Support for Other Files
This package supports a plugin design pattern to dynamically resolve how to parse individual files. 

### Creating a New Plugin
You can create a new plugin by using the `AbstractFileParser` class from `vega.packaging.parsers` to create a new class.

Key class-level attributes:
* **`FILENAME_REGEX`** — Regex pattern matched against filenames to identify which parser handles which file.
* **`IS_BUILD_FILE`** — Set to `True` if this file represents a buildable package (enables `build_and_publish` support).
* **`BUILD_TYPE`** — A `const.BuildTypes` enum value identifying the build ecosystem (e.g. `BuildTypes.RUST`).
* **`RELEASE_PATH`** — Directory (relative to the parser file's directory) where release artifacts are staged. Set to `None` if this build type has no release artifacts.
* **`PRIORITY`** — Parse/update order; lower number = higher priority.

Key methods to implement:
* **`build()`** — Build the package (e.g. `cargo package`, `pip wheel`).
* **`publish()`** — Publish the package to a registry.
* **`release()`** — Compile/stage release artifacts (e.g. cross-compiled binaries) under `RELEASE_PATH`. Called by `build_and_publish --compile_only`.


#### Example
```python
import re
import subprocess

from vega.packaging import commits
from vega.packaging import const
from vega.packaging import contextmanagers
from vega.packaging import decorators
from vega.packaging.parsers import abstract_parser


class MyNewFileParser(abstract_parser.AbstractFileParser):
    # FILENAME_REGEX is the key used to resolve which parser goes with which file
    # Regex is used to accommodate for dynamic names, multiple names and to ignore casing.
    FILENAME_REGEX = re.compile("somefilename.txt", re.I)
    # PRIORITY is to determine the parsing priority order of the file, with 1 being the highest
    PRIORITY = 3
    # AUTOCREATE determines if the file should be created if it isn't found on disk. Default is True.
    AUTOCREATE = False
    # TEMPLATE is the contents of what a new file generated file should contain
    TEMPLATE = "Hello World!"
    # DEFAULT_VERSION is the version that should be returned when no version is found. The default value is 0.0.0

    # Build-related attributes (set these to enable build_and_publish support)
    IS_BUILD_FILE = True  # Set True to enable build/publish/release support
    BUILD_TYPE = const.BuildTypes.CUSTOM  # Define a new BuildType or use existing
    RELEASE_PATH = None  # Set to directory name if build produces release artifacts (e.g., "bin")

    # There are 4 methods that need to be reimplemented from the abstract method.

    # The version property is how you get the version associated with this file
    @property
    def version(self) -> str:
        """Gets the semantic version from this file"""
        if not self._version:
            regex = re.search("My Version is (?P<version>[0-9]+.[0-9]+.[0-9]+)", self.content)
            self._version = regex.group("version") if regex else self.DEFAULT_VERSION
        return self._version

    # The create method is for creating a new version of this file using the template
    def create(self):
        """Creates a new file with the contents of the template."""
        with open(self.path, "w+") as handle:
            handle.write(self.TEMPLATE)

    # Reads the content of the file.
    # The content property should be used to access the data as it is cached in memory.
    # The content property uses the read property to read the contents of the file.
    def read(self):
        """Creates a new file with the contents of the template."""
        with open(self.path, "r+") as handle:
            return handle.read(self.path)

    # The update method updates the content of the file based on the data from the commit message.
    # The file should be overwritten at the end of this method.
    # The autocreate decorator is for raising an error if the file doesn't exist if AUTOCREATE is false and to create it
    # if AUTOCREATE is True
    @decorators.autocreate
    def update(self, commit_message: commits.CommitMessage):
        """Updates the content of the file based on the commit message.

        Args:
          commit_message: the message to use for updating the file
        """
        # Updates the semantic version of this file
        # If the commit message doesn't have a semantic version resolved and has a pending bump
        # then the update_version method will update the semantic version of the commit message based on the bump version value.
        #
        self.update_version(commit_message)

        # Add semantic version environment variable to the GitHub env
        regex = re.compile("My Version is (?P<version>[0-9]+.[0-9]+.[0-9]+)")
        if regex.search(self.content):
            content = regex.sub(commit_message.semantic_version, self.content)
        else:
            content = f"{self.content}\nMy Version is {commit_message.semantic_version}"

        # Update the file
        with open(self.path, "w+") as handle:
            handle.write(content)

        # Reset the values of the object so they get parsed again data is queried from it.
        # Note: This isn't required if the content data is mutable, and really only required if the data is unmutable
        #       like in this example

        self.reset()

    def build(self, commit_message=None):
        """Builds the package.

        This method is called by build_and_publish when --publish or --release is used.
        Use WorkingDirectory context manager to ensure subprocess runs from the package directory.
        """
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            # Example: run a custom build command
            result = subprocess.run(
                ["mybuildtool", "build"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Build failed: {result.stderr}")
            # Store the build artifact path (relative to package directory)
            self._build = "dist/package.zip"

    def publish(self, registry=None):
        """Publishes the package to a registry.

        This method is called by build_and_publish after all builds complete successfully.
        Use WorkingDirectory context manager to ensure subprocess runs from the package directory.
        """
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            registry = registry or self._registry
            if not self._build:
                raise RuntimeError("Must build before publishing")
            # Example: publish to a registry
            cmd = ["mybuildtool", "publish", self._build]
            if registry:
                cmd.extend(["--registry", registry])
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Publish failed: {result.stderr}")

    def release(self):
        """Stages release artifacts for GitHub/GitLab release.

        This method is called by build_and_publish when --compile_only is used.
        Use WorkingDirectory context manager to ensure subprocess runs from the package directory.
        Artifacts should be placed in the directory specified by RELEASE_PATH.
        """
        with contextmanagers.WorkingDirectory(self.path, is_file=True):
            # Example: compile release binaries and stage them
            result = subprocess.run(
                ["mybuildtool", "release"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Release build failed: {result.stderr}")
            # Artifacts are staged under RELEASE_PATH directory (e.g., "bin/")
            # and will be attached to the GitHub/GitLab release by build_and_publish
```

### Making the Plugin Discoverable 
You can make the file discoverable doing either of the following steps: 
1. Adding the file to the **vega.packaging.parsers** directory<br><br>

2. Setting the **PACKAGING_FILE_PARSERS** environment variable to the directory where the file should be discovered. 
   * Note: When using the environment variable, the package will dynamically import *ALL* the files in the directory.<br><br>
   Be careful about other python files in this directory for unintended code that might be ran upon loading the plugins. 

Once the plugin is discoverable, the cli command and factory method will be able to discover the files and updated them
accordingly based on the logic introduced in the plugin.
