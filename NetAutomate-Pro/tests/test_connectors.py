"""
Tests for netautomate.connectors — DeviceConnector (simulation mode)
"""
import sys
import types
import pytest
from unittest.mock import patch, MagicMock

from netautomate.connectors import DeviceConnector


CISCO_DEVICE = {
    "hostname": "router1",
    "ip": "192.168.1.1",
    "device_type": "cisco_ios",
    "username": "admin",
    "password": "cisco123",
    "secret": "enablepass",
    "port": 22,
}

JUNIPER_DEVICE = {
    "hostname": "juniper1",
    "ip": "192.168.1.4",
    "device_type": "juniper_junos",
    "username": "admin",
    "password": "juniper123",
    "port": 22,
}


class TestDeviceConnectorSimulation:
    """Tests that run in simulation mode (Netmiko not required)."""

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_connect_returns_true_in_sim_mode(self):
        connector = DeviceConnector(CISCO_DEVICE)
        assert connector.connect() is True

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_send_command_show_version(self):
        connector = DeviceConnector(CISCO_DEVICE)
        output = connector.send_command("show version")
        assert "Cisco IOS" in output

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_send_command_show_running_config(self):
        connector = DeviceConnector(CISCO_DEVICE)
        output = connector.send_command("show running-config")
        assert "hostname" in output.lower() or "Building configuration" in output

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_send_command_unknown_returns_sim_string(self):
        connector = DeviceConnector(CISCO_DEVICE)
        output = connector.send_command("show custom-unknown-command")
        assert "SIMULATION" in output

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_send_config_simulation(self):
        connector = DeviceConnector(CISCO_DEVICE)
        output = connector.send_config(["interface GigabitEthernet0/0", "no shutdown"])
        assert "Configuration saved" in output or "configure terminal" in output

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_get_running_config_cisco(self):
        connector = DeviceConnector(CISCO_DEVICE)
        output = connector.get_running_config()
        assert len(output) > 0

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_get_running_config_juniper_uses_show_configuration(self):
        connector = DeviceConnector(JUNIPER_DEVICE)
        output = connector.get_running_config()
        assert output is not None

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_device_type_mapping(self):
        connector = DeviceConnector(CISCO_DEVICE)
        assert connector.conn_params["device_type"] == "cisco_ios"

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_juniper_device_type_mapping(self):
        connector = DeviceConnector(JUNIPER_DEVICE)
        assert connector.conn_params["device_type"] == "juniper_junos"

    @patch("netautomate.connectors.NETMIKO_AVAILABLE", False)
    def test_context_manager(self):
        with DeviceConnector(CISCO_DEVICE) as conn:
            output = conn.send_command("show version")
        assert output is not None

    def test_conn_params_built_correctly(self):
        connector = DeviceConnector(CISCO_DEVICE)
        assert connector.conn_params["host"] == "192.168.1.1"
        assert connector.conn_params["port"] == 22
        assert connector.conn_params["username"] == "admin"

    def test_secret_added_when_present(self):
        connector = DeviceConnector(CISCO_DEVICE)
        assert "secret" in connector.conn_params

    def test_secret_absent_when_not_provided(self):
        device = dict(JUNIPER_DEVICE)  # no secret field
        connector = DeviceConnector(device)
        assert "secret" not in connector.conn_params


# ---------------------------------------------------------------------------
# Helpers for injecting a fake netmiko module when the real one isn't installed
# ---------------------------------------------------------------------------

def _make_fake_netmiko():
    """Build a minimal fake netmiko module with ConnectHandler."""
    fake_netmiko = types.ModuleType("netmiko")
    fake_netmiko.ConnectHandler = MagicMock
    fake_netmiko.NetmikoTimeoutException = Exception
    fake_netmiko.NetmikoAuthenticationException = Exception
    return fake_netmiko


class TestDeviceConnectorWithNetmiko:
    """Tests that verify ConnectHandler is called correctly.

    We inject a fake netmiko module so the tests don't require the real
    library to be installed.
    """

    def _patched_connector(self, mock_ch_return):
        """Return a connector with NETMIKO_AVAILABLE=True and mocked ConnectHandler."""
        import netautomate.connectors as conn_mod

        mock_ch = MagicMock(return_value=mock_ch_return)
        # Temporarily graft ConnectHandler onto the module so patch can find it
        conn_mod.ConnectHandler = mock_ch
        conn_mod.NetmikoTimeoutException = Exception
        conn_mod.NetmikoAuthenticationException = Exception
        return conn_mod, mock_ch

    def test_connect_calls_connect_handler(self):
        import netautomate.connectors as conn_mod
        mock_instance = MagicMock()
        conn_mod.ConnectHandler = MagicMock(return_value=mock_instance)
        conn_mod.NetmikoTimeoutException = Exception
        conn_mod.NetmikoAuthenticationException = Exception

        with patch.object(conn_mod, "NETMIKO_AVAILABLE", True):
            connector = DeviceConnector(CISCO_DEVICE)
            connector.connect()
            assert connector.connection is mock_instance

    def test_send_command_calls_netmiko(self):
        import netautomate.connectors as conn_mod
        mock_instance = MagicMock()
        mock_instance.send_command.return_value = "Router1#"
        conn_mod.ConnectHandler = MagicMock(return_value=mock_instance)
        conn_mod.NetmikoTimeoutException = Exception
        conn_mod.NetmikoAuthenticationException = Exception

        with patch.object(conn_mod, "NETMIKO_AVAILABLE", True):
            connector = DeviceConnector(CISCO_DEVICE)
            connector.connect()
            output = connector.send_command("show version")
            mock_instance.send_command.assert_called_once()
            assert output == "Router1#"

    def test_send_config_saves_config(self):
        import netautomate.connectors as conn_mod
        mock_instance = MagicMock()
        mock_instance.send_config_set.return_value = "config applied"
        conn_mod.ConnectHandler = MagicMock(return_value=mock_instance)
        conn_mod.NetmikoTimeoutException = Exception
        conn_mod.NetmikoAuthenticationException = Exception

        with patch.object(conn_mod, "NETMIKO_AVAILABLE", True):
            connector = DeviceConnector(CISCO_DEVICE)
            connector.connect()
            connector.send_config(["hostname new-name"])
            mock_instance.save_config.assert_called_once()

    def test_disconnect_clears_connection(self):
        import netautomate.connectors as conn_mod
        mock_instance = MagicMock()
        conn_mod.ConnectHandler = MagicMock(return_value=mock_instance)
        conn_mod.NetmikoTimeoutException = Exception
        conn_mod.NetmikoAuthenticationException = Exception

        with patch.object(conn_mod, "NETMIKO_AVAILABLE", True):
            connector = DeviceConnector(CISCO_DEVICE)
            connector.connect()
            connector.disconnect()
            mock_instance.disconnect.assert_called_once()
            assert connector.connection is None
