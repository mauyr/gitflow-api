class GitflowError(Exception):
    """Base error for the modernized gitflow-api domain."""


class ConfigError(GitflowError):
    """Raised when configuration is invalid or incomplete."""


class RepositoryError(GitflowError):
    """Raised for local git repository errors."""


class WorkingTreeNotCleanError(RepositoryError):
    """Raised when the repository has uncommitted changes and the action requires a clean tree."""


class BranchAlreadyExistsError(RepositoryError):
    """Raised when a branch already exists."""


class BranchNotFoundError(RepositoryError):
    """Raised when a branch cannot be found."""


class ProviderError(GitflowError):
    """Raised when the remote provider fails."""


class UnsupportedProviderError(ProviderError):
    """Raised when the configured provider is not supported by the current build."""


class MergeRequestNotFoundError(ProviderError):
    """Raised when a merge request cannot be resolved."""


class MergeRequestNotReadyError(ProviderError):
    """Raised when a merge request exists but is not mergeable yet."""


class ChangelogError(GitflowError):
    """Raised when changelog generation fails."""


class ReleaseFlowError(GitflowError):
    """Raised when the configured repository cannot execute the requested release flow."""
