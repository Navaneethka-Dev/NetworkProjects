"""Compliance API — /api/compliance/*

Runs pattern-based security checks against each device's running configuration.
In MOCK_DEVICES mode (default) a simulated config is returned from the connector;
in real mode it SSHes via Netmiko and grabs `show running-config`.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db
from app.core.rbac import require_viewer
from app.models.device import Device, DeviceStatusEnum
from app.network.connector import DeviceConnector

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

# ── Built-in rules (mirrors configs/standards.yaml + frontend constants) ───────

BUILT_IN_RULES: list[dict[str, Any]] = [
    {"id": "r1",  "name": "SSH Enabled",          "description": "SSH must be enabled on VTY lines",                "severity": "critical", "category": "Security",       "pattern": "transport input ssh",              "required": True},
    {"id": "r2",  "name": "Enable Secret",         "description": "Enable secret should be configured",              "severity": "critical", "category": "Security",       "pattern": "enable secret",                    "required": True},
    {"id": "r3",  "name": "No Telnet",             "description": "Telnet must be disabled",                         "severity": "high",     "category": "Security",       "pattern": "transport input telnet",           "required": False},
    {"id": "r4",  "name": "NTP Configured",        "description": "NTP server must be configured",                   "severity": "high",     "category": "Compliance",     "pattern": "ntp server",                       "required": True},
    {"id": "r5",  "name": "Logging Enabled",       "description": "Syslog server must be configured",                "severity": "high",     "category": "Observability",  "pattern": "logging host",                     "required": True},
    {"id": "r6",  "name": "SNMP Community",        "description": "SNMP community strings should be set",            "severity": "medium",   "category": "Observability",  "pattern": "snmp-server community",            "required": True},
    {"id": "r7",  "name": "Password Encryption",   "description": "Service password-encryption must be on",          "severity": "high",     "category": "Security",       "pattern": "service password-encryption",       "required": True},
    {"id": "r8",  "name": "Banner MOTD",           "description": "Login banner must be configured",                 "severity": "low",      "category": "Compliance",     "pattern": "banner motd",                      "required": True},
    {"id": "r9",  "name": "AAA New-model",         "description": "AAA new-model must be enabled",                   "severity": "critical", "category": "Security",       "pattern": "aaa new-model",                    "required": True},
    {"id": "r10", "name": "Spanning-tree Guard",   "description": "Spanning-tree portfast bpduguard default",        "severity": "medium",   "category": "Network",        "pattern": "spanning-tree portfast bpduguard default", "required": True},
    {"id": "r11", "name": "IPv6 Routing",          "description": "IPv6 should be explicitly configured",            "severity": "low",      "category": "Network",        "pattern": "ipv6 unicast-routing",             "required": True},
]


def _check_config(config: str, rules: list[dict]) -> list[dict]:
    """Return per-rule pass/fail results against a config string."""
    results = []
    config_lower = config.lower()
    for rule in rules:
        pattern = rule["pattern"].lower()
        found_pattern = pattern if pattern in config_lower else None
        # For "required: False" rules (like No Telnet), pass means the pattern is NOT present.
        if not rule["required"]:
            passed = found_pattern is None
            found_pattern = rule["pattern"] if not passed else None
        else:
            passed = found_pattern is not None
        results.append({
            "rule": rule,
            "passed": passed,
            "found": found_pattern,
        })
    return results


def _audit_device(device: Device, rules: list[dict]) -> dict:
    """Run compliance checks against a single device and return structured result."""
    dev_dict = {
        "hostname": device.hostname,
        "ip_address": device.ip_address,
        "device_type": device.device_type,
        "vendor": device.vendor,
        "username": device.username,
        "password": "simulated",
        "ssh_port": device.ssh_port,
    }

    connector = DeviceConnector(dev_dict)
    config = ""
    error = None
    try:
        config = connector.get_running_config()
    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    checks = _check_config(config, rules) if config else [
        {"rule": r, "passed": False, "found": None} for r in rules
    ]

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round((passed_count / total) * 100) if total else 0
    compliant = score >= 80

    return {
        "device_id": str(device.id),
        "hostname": device.hostname,
        "ip_address": device.ip_address,
        "vendor": device.vendor,
        "device_type": device.device_type,
        "status": device.status.value,
        "score": score,
        "compliant": compliant,
        "passed_checks": passed_count,
        "total_checks": total,
        "error": error,
        "checks": checks,
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/rules")
async def get_rules(_=Depends(require_viewer)):
    """Return the built-in compliance rule set."""
    return BUILT_IN_RULES


@router.get("/run")
async def run_compliance(
    device_id: uuid.UUID | None = Query(None, description="Audit a single device; omit for all"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    """
    Execute compliance checks against one or all devices.

    Uses simulation mode unless ``MOCK_DEVICES=false`` in the environment
    and Netmiko is installed.
    """
    if device_id:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        devices = [device]
    else:
        result = await db.execute(select(Device))
        devices = list(result.scalars().all())

    audit_results = [_audit_device(d, BUILT_IN_RULES) for d in devices]

    # Fleet-level summary
    total_devices = len(audit_results)
    compliant_count = sum(1 for r in audit_results if r["compliant"])
    avg_score = round(sum(r["score"] for r in audit_results) / total_devices) if total_devices else 0
    total_checks = sum(r["total_checks"] for r in audit_results)
    passed_checks = sum(r["passed_checks"] for r in audit_results)
    critical_fails = sum(
        1 for r in audit_results
        for c in r["checks"]
        if not c["passed"] and c["rule"]["severity"] == "critical"
    )

    return {
        "summary": {
            "total_devices": total_devices,
            "compliant_devices": compliant_count,
            "non_compliant_devices": total_devices - compliant_count,
            "avg_score": avg_score,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "critical_failures": critical_fails,
            "mock_mode": settings.MOCK_DEVICES,
        },
        "results": audit_results,
    }
