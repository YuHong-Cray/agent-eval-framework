"""Tests for Docker sandbox manager."""
from pathlib import Path

import pytest

from eval_framework.sandbox.manager import SandboxManager
from eval_framework.sandbox.snapshot import FilesystemSnapshot


class TestFilesystemSnapshot:
    def test_detect_new_file(self, tmp_path):
        """Snapshot diff should detect newly created files."""
        before = FilesystemSnapshot.capture(tmp_path)
        new_file = tmp_path / "created.txt"
        new_file.write_text("hello")
        after = FilesystemSnapshot.capture(tmp_path)

        diff = FilesystemSnapshot.diff(before, after)
        assert "created.txt" in diff.created_files

    def test_detect_modified_file(self, tmp_path):
        """Snapshot diff should detect modified files."""
        f = tmp_path / "modify.txt"
        f.write_text("before")
        before = FilesystemSnapshot.capture(tmp_path)
        f.write_text("after")
        after = FilesystemSnapshot.capture(tmp_path)

        diff = FilesystemSnapshot.diff(before, after)
        assert "modify.txt" in diff.modified_files

    def test_detect_deleted_file(self, tmp_path):
        """Snapshot diff should detect deleted files."""
        f = tmp_path / "delete_me.txt"
        f.write_text("gone")
        before = FilesystemSnapshot.capture(tmp_path)
        f.unlink()
        after = FilesystemSnapshot.capture(tmp_path)

        diff = FilesystemSnapshot.diff(before, after)
        assert "delete_me.txt" in diff.deleted_files
