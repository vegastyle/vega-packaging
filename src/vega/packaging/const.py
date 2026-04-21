import enum 


class Versions(enum.Enum):
    """ Enums for the different semantic verions"""
    MAJOR = 0
    MINOR = 1
    PATCH = 2


class Changes(enum.Enum):
    """Enum for the different possible changelog categories as determined by Keepchangelog.com"""
    # Keepchangelog.com standard changes
    ADDED = "added"
    CHANGED = "changed"
    DEPRECATED = "deprecated"
    REMOVED = "removed"
    FIXED = "fixed"
    SECURITY = "security"

    # Custom tags for indicating other changes
    UPDATED = "changed"

class BuildTypes(enum.Enum):
    PYTHON = "python"
    NPM = "npm"
    DOCKER = "docker"
    RUST = "rust"

class WorkflowTypes(enum.Enum):
    IGNORE = "ignore"
    PUBLISH = "publish"
    RELEASE = "release"

class Platforms(enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"

class Builds(enum.Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

