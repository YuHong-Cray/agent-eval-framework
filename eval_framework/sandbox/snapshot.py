"""Filesystem snapshot for detecting agent-made changes."""

import dataclasses
import hashlib
from pathlib import Path


@dataclasses.dataclass
class SnapshotDiff:
    created_files: list[str]
    modified_files: list[str]
    deleted_files: list[str]

    @property
    def has_changes(self) -> bool:
        return any([self.created_files, self.modified_files, self.deleted_files])


class FilesystemSnapshot:
    """Captures file hashes of a directory and computes diffs."""

    def __init__(self, files: dict[str, str]):
        self._files = files  # relative_path -> sha256 hex

    @classmethod
    def capture(cls, root: Path) -> "FilesystemSnapshot":
        """Capture all file hashes recursively under root."""
        files = {}
        root = root.resolve()
        for path in root.rglob("*"):
            if path.is_file() and ".git" not in path.parts:
                rel = str(path.relative_to(root))
                files[rel] = cls._hash_file(path)
        return cls(files)

    @staticmethod
    def _hash_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @classmethod
    def diff(
        cls, before: "FilesystemSnapshot", after: "FilesystemSnapshot"
    ) -> SnapshotDiff:
        """Compare two snapshots and return the diff."""
        before_files = set(before._files.keys())
        after_files = set(after._files.keys())

        created = sorted(after_files - before_files)
        deleted = sorted(before_files - after_files)
        modified = sorted(
            f
            for f in before_files & after_files
            if before._files[f] != after._files[f]
        )
        return SnapshotDiff(
            created_files=created,
            modified_files=modified,
            deleted_files=deleted,
        )
