"""Network device connector — real Netmiko or simulation mode."""
from __future__ import annotations

import random
import time
from typing import Any

from app.config import settings

try:
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False


# ── Simulation responses ───────────────────────────────────────────────────────

_SIM_SHOW_VERSION = {
    "cisco_ios": (
        "Cisco IOS Software, Version 15.7(3)M5, RELEASE SOFTWARE\n"
        "ROM: Bootstrap program is IOSv\nHostname: {hostname}\n"
        "Uptime: 42 days, 6 hours, 14 minutes\n"
        "Processor board ID FAKESN123456"
    ),
    "juniper_junos": (
        "Junos: 21.3R1.9\nModel: {hostname}\n"
        "JUNOS Base OS boot [21.3R1.9]\nUptime: 42 days"
    ),
}

_SIM_RUNNING_CONFIG = {
    "cisco": (
        "! Current configuration\nhostname {hostname}\n"
        "ip ssh version 2\nservice password-encryption\n"
        "enable secret 5 $1$mERr$encrypted\n"
        "no ip http server\nno ip http secure-server\n"
        "banner motd ^ Authorized access only ^\n"
        "logging buffered 16384\nlogging host 10.0.0.2\n"
        "ntp server 10.0.0.1\nsnmp-server community public RO\n"
        "line vty 0 4\n login local\n transport input ssh\n exec-timeout 5 0\n"
    ),
    "juniper": (
        "## Juniper configuration for {hostname}\n"
        "system {{\n    host-name {hostname};\n    services {{ ssh; }}\n"
        "    syslog {{ file messages {{ any notice; }} }}\n}}\n"
    ),
}


class DeviceConnector:
    """Thin wrapper around Netmiko with transparent simulation mode."""

    def __init__(self, device: dict[str, Any]) -> None:
        self.hostname = device.get("hostname", "unknown")
        self.device_type = device.get("device_type", "cisco_ios")
        self.vendor = device.get("vendor", "cisco")
        self.mock = settings.MOCK_DEVICES or not NETMIKO_AVAILABLE
        self._conn_params = {
            "device_type": self.device_type,
            "host": device["ip_address"],
            "username": device["username"],
            "password": device["password"],
            "port": device.get("ssh_port", 22),
            "timeout": settings.DEVICE_SSH_TIMEOUT,
        }
        if device.get("secret"):
            self._conn_params["secret"] = device["secret"]
        self._connection = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        if self.mock:
            return True
        try:
            self._connection = ConnectHandler(**self._conn_params)
            return True
        except Exception:
            return False

    def disconnect(self) -> None:
        if self._connection:
            try:
                self._connection.disconnect()
            except Exception:
                pass
            self._connection = None

    def send_command(self, command: str) -> str:
        if self.mock:
            return self._sim_command(command)
        if not self._connection:
            self.connect()
        return self._connection.send_command(command)

    def send_config(self, commands: list[str]) -> str:
        if self.mock:
            joined = "\n".join(commands)
            return f"[SIMULATION] Configured {len(commands)} lines on {self.hostname}:\n{joined}"
        if not self._connection:
            self.connect()
        output = self._connection.send_config_set(commands)
        self._connection.save_config()
        return output

    def get_running_config(self) -> str:
        cmd = "show configuration" if "juniper" in self.device_type else "show running-config"
        return self.send_command(cmd)

    def ping(self) -> tuple[bool, float | None]:
        """Returns (reachable, latency_ms)."""
        if self.mock:
            latency = round(random.uniform(1.5, 45.0), 2)
            return True, latency
        start = time.perf_counter()
        ok = self.connect()
        self.disconnect()
        if ok:
            return True, round((time.perf_counter() - start) * 1000, 2)
        return False, None

    def __enter__(self) -> "DeviceConnector":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.disconnect()

    # ── Simulation helpers ─────────────────────────────────────────────────────

    def _sim_command(self, command: str) -> str:
        cmd = command.lower().strip()
        vendor_key = "juniper" if "juniper" in self.device_type else "cisco"
        if "show version" in cmd:
            tmpl = _SIM_SHOW_VERSION.get(self.device_type, _SIM_SHOW_VERSION["cisco_ios"])
            return tmpl.format(hostname=self.hostname)
        if "running" in cmd or "configuration" in cmd:
            tmpl = _SIM_RUNNING_CONFIG.get(vendor_key, _SIM_RUNNING_CONFIG["cisco"])
            return tmpl.format(hostname=self.hostname)
        if "interface" in cmd:
            return (
                f"GigabitEthernet0/0  192.168.1.1  YES NVRAM  up  up\n"
                f"GigabitEthernet0/1  unassigned   YES NVRAM  up  down"
            )
        if "bgp" in cmd:
            return f"BGP router identifier 10.0.0.1, local AS number 65001\nNeighbor 10.0.0.2 AS 65002  Up/Down: 5d"
        return f"[SIMULATION] {self.hostname}# {command}\n% Command executed (simulation mode)"
