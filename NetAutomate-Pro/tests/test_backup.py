"""
Tests for netautomate.backup — BackupManager
"""
import os
import time
import tempfile
from pathlib import Path
import pytest

from netautomate.backup import BackupManager


@pytest.fixture
def tmp_backup_dir(tmp_path):
    return str(tmp_path / "backups")


@pytest.fixture
def manager(tmp_backup_dir):
    return BackupManager(backup_dir=tmp_backup_dir)


class TestBackupManager:
    def test_save_backup_creates_file(self, manager, tmp_backup_dir):
        path = manager.save_backup("router1", "! running config\nhostname router1\n")
        assert os.path.exists(path)
        assert "router1" in path
        assert path.endswith(".cfg")

    def test_save_backup_with_suffix(self, manager):
        path = manager.save_backup("switch1", "! config", suffix="pre_deploy")
        assert "pre_deploy" in path

    def test_save_backup_contains_header(self, manager):
        path = manager.save_backup("router2", "hostname router2")
        content = Path(path).read_text(encoding="utf-8")
        assert "NetAutomate Pro" in content
        assert "router2" in content

    def test_get_latest_backup_returns_most_recent(self, manager):
        manager.save_backup("router1", "! config v1", suffix="v1")
        manager.save_backup("router1", "! config v2", suffix="v2")
        latest = manager.get_latest_backup("router1")
        assert latest is not None
        assert "router1" in latest

    def test_get_latest_backup_nonexistent_device(self, manager):
        result = manager.get_latest_backup("nonexistent")
        assert result is None

    def test_list_backups_all(self, manager):
        manager.save_backup("router1", "c1", suffix="a")
        manager.save_backup("switch1", "c2", suffix="b")
        backups = manager.list_backups()
        assert len(backups) == 2
        hostnames = {b["hostname"] for b in backups}
        assert "router1" in hostnames
        assert "switch1" in hostnames

    def test_list_backups_filtered(self, manager):
        manager.save_backup("router1", "c1", suffix="x")
        manager.save_backup("switch1", "c2", suffix="y")
        backups = manager.list_backups(hostname="router1")
        assert len(backups) == 1
        assert backups[0]["hostname"] == "router1"

    def test_list_backups_returns_metadata(self, manager):
        manager.save_backup("router1", "hostname router1")
        backups = manager.list_backups()
        b = backups[0]
        assert "filename" in b
        assert "size" in b
        assert "modified" in b
        assert b["size"] > 0

    def test_get_backup_content(self, manager):
        path = manager.save_backup("router1", "hostname router1")
        content = manager.get_backup_content(path)
        assert "hostname router1" in content

    def test_compare_backups_detects_changes(self, manager):
        # Use suffixes to guarantee unique filenames even within the same second
        p1 = manager.save_backup(
            "router1",
            "hostname router1\nip ssh version 2",
            suffix="snap1"
        )
        p2 = manager.save_backup(
            "router1",
            "hostname router1\nno ip http server",
            suffix="snap2"
        )
        diff = manager.compare_backups(p1, p2)
        assert "added" in diff
        assert "removed" in diff
        assert "unchanged_count" in diff
        # "ip ssh version 2" removed; "no ip http server" added → at least 1 change
        assert diff["total_changes"] >= 1

    def test_cleanup_old_backups(self, manager):
        # Use distinct suffixes so filenames are always unique
        for i in range(5):
            manager.save_backup("router1", f"! config v{i}", suffix=f"v{i}")
        backups_before = manager.list_backups(hostname="router1")
        assert len(backups_before) == 5
        manager.cleanup_old_backups(hostname="router1", keep_count=2)
        remaining = manager.list_backups(hostname="router1")
        assert len(remaining) == 2
