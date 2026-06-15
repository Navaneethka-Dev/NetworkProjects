"""
Integration tests for netautomate.core — NetworkAutomation
Uses simulation mode (no real devices required).
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from netautomate.core import NetworkAutomation


# ── Fixtures ─────────────────────────────────────────────────────────────────

INVENTORY_YAML = """\
devices:
  - hostname: router1
    ip: 192.168.1.1
    device_type: cisco_ios
    username: admin
    password: cisco123
    secret: enablepass
    port: 22

  - hostname: switch1
    ip: 192.168.1.2
    device_type: cisco_ios
    username: admin
    password: cisco123
    secret: enablepass
    port: 22

  - hostname: juniper1
    ip: 192.168.1.4
    device_type: juniper_junos
    username: admin
    password: juniper123
    port: 22
"""

VLAN_TEMPLATE = """\
vlan {{ vlan_id }}
 name {{ vlan_name | default('DEFAULT') }}
"""


@pytest.fixture
def inv_file(tmp_path):
    """Write a temporary inventory YAML and return its path."""
    p = tmp_path / "devices.yaml"
    p.write_text(INVENTORY_YAML, encoding="utf-8")
    return str(p)


@pytest.fixture
def template_file(tmp_path):
    """Write a minimal Jinja2 template and return its path."""
    t = tmp_path / "vlan.j2"
    t.write_text(VLAN_TEMPLATE, encoding="utf-8")
    return str(t)


@pytest.fixture
def na(inv_file, tmp_path):
    """NetworkAutomation instance pointing at a temp backup dir."""
    from netautomate.backup import BackupManager
    instance = NetworkAutomation(inv_file)
    # Redirect backups to a temp directory so we don't pollute the workspace
    instance.backup_manager = BackupManager(backup_dir=str(tmp_path / "backups"))
    return instance


# ── Inventory loading ─────────────────────────────────────────────────────────

class TestInventoryLoading:
    def test_loads_correct_device_count(self, na):
        assert len(na.devices) == 3

    def test_device_hostnames_present(self, na):
        hostnames = [d["hostname"] for d in na.devices]
        assert "router1" in hostnames
        assert "switch1" in hostnames
        assert "juniper1" in hostnames

    def test_list_devices_returns_all(self, na):
        devices = na.list_devices()
        assert len(devices) == 3

    def test_missing_inventory_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            NetworkAutomation(str(tmp_path / "nonexistent.yaml"))

    def test_get_device_by_hostname(self, na):
        device = na._get_device("router1")
        assert device is not None
        assert device["ip"] == "192.168.1.1"

    def test_get_device_unknown_returns_none(self, na):
        assert na._get_device("unknown-host") is None


# ── Backup ────────────────────────────────────────────────────────────────────

class TestBackupOperations:
    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_backup_device_success(self, na):
        result = na.backup_device("router1")
        assert result["status"] == "success"
        assert "backup_file" in result
        assert os.path.exists(result["backup_file"])

    def test_backup_device_unknown_host(self, na):
        result = na.backup_device("nonexistent")
        assert result["status"] == "failed"
        assert "not found" in result["error"]

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_backup_all_devices(self, na):
        results = na.backup_all_devices(max_workers=2)
        assert len(results) == 3
        statuses = {r["status"] for r in results}
        assert "success" in statuses

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_backup_all_returns_device_key(self, na):
        results = na.backup_all_devices()
        for r in results:
            assert "device" in r


# ── Deploy ────────────────────────────────────────────────────────────────────

class TestDeployOperations:
    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_deploy_dry_run_returns_preview(self, na, template_file):
        result = na.deploy_config(
            "router1",
            template_file,
            variables={"vlan_id": 100, "vlan_name": "PROD"},
            dry_run=True,
        )
        assert result["status"] == "success"
        assert result["mode"] == "dry-run"
        assert "vlan 100" in result["config_preview"].lower() or \
               "100" in result["config_preview"]

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_deploy_config_live(self, na, template_file):
        result = na.deploy_config(
            "router1",
            template_file,
            variables={"vlan_id": 200},
            dry_run=False,
        )
        assert result["status"] == "success"

    def test_deploy_unknown_host(self, na, template_file):
        result = na.deploy_config("ghost-host", template_file)
        assert result["status"] == "failed"

    def test_deploy_missing_template(self, na):
        result = na.deploy_config("router1", "/nonexistent/template.j2")
        assert result["status"] == "failed"

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_deploy_to_all(self, na, template_file):
        results = na.deploy_to_all(template_file, {"vlan_id": 10}, dry_run=True)
        assert len(results) == 3
        for r in results:
            assert r["status"] == "success"
            assert "device" in r


# ── Execute command ───────────────────────────────────────────────────────────

class TestExecuteCommand:
    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_execute_show_version(self, na):
        result = na.execute_command("router1", "show version")
        assert result["status"] == "success"
        assert "Cisco" in result["output"]

    def test_execute_unknown_host(self, na):
        result = na.execute_command("ghost", "show version")
        assert result["status"] == "failed"
        assert "not found" in result["error"]

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_execute_arbitrary_command(self, na):
        result = na.execute_command("router1", "show ip interface brief")
        assert result["status"] == "success"
        assert len(result["output"]) > 0


# ── Compliance ────────────────────────────────────────────────────────────────

class TestComplianceOperations:
    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_check_compliance_single(self, na):
        result = na.check_compliance("router1")
        assert "score" in result
        assert "compliant" in result
        assert isinstance(result["score"], int)

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_check_compliance_all(self, na):
        results = na.check_compliance_all()
        assert len(results) == 3
        for r in results:
            assert "score" in r

    def test_check_compliance_unknown_host(self, na):
        result = na.check_compliance("ghost")
        assert result.get("status") == "failed"

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_compliance_score_range(self, na):
        result = na.check_compliance("router1")
        assert 0 <= result["score"] <= 100


# ── Ping / Health ─────────────────────────────────────────────────────────────

class TestPingDevice:
    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_ping_known_device_returns_true(self, na):
        result = na.ping_device("router1")
        assert result is True

    def test_ping_unknown_device_returns_false(self, na):
        result = na.ping_device("nonexistent")
        assert result is False

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_ping_all_devices(self, na):
        results = [na.ping_device(d["hostname"]) for d in na.devices]
        assert all(isinstance(r, bool) for r in results)
        assert any(r is True for r in results)
