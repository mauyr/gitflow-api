from dataclasses import dataclass


@dataclass(frozen=True)
class GitCommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class RemoteProjectRef:
    host: str
    namespace: str
    project: str
    full_path: str
