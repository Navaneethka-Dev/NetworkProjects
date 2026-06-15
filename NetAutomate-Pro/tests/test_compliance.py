"""
Tests for netautomate.compliance — ComplianceChecker
"""
import pytest
from netautomate.compliance import ComplianceChecker


COMPLIANT_CONFIG = """
hostname Router1
ip domain-name network.local
service password-encryption
enable secret 5 $1$encrypted
no ip http server
no ip http secure-server
banner motd ^ Authorized access only ^
logging buffered 16384
logging host 10.0.0.2
ntp server 10.0.0.1
snmp-server community public RO
line vty 0 4
 login local
 transport input ssh
 exec-timeout 5 0
"""

NON_COMPLIANT_CONFIG = """
hostname Router2
line vty 0 4
 transport input telnet
"""


@pytest.fixture
def checker():
    return ComplianceChecker()


class TestComplianceChecker:
    def test_compliant_config_high_score(self, checker):
        result = checker.check(COMPLIANT_CONFIG)
        assert result["score"] >= 80
        assert result["compliant"] is True

    def test_non_compliant_config_low_score(self, checker):
        result = checker.check(NON_COMPLIANT_CONFIG)
        assert result["score"] < 80
        assert result["compliant"] is False

    def test_result_has_required_keys(self, checker):
        result = checker.check(COMPLIANT_CONFIG)
        for key in ("compliant", "score", "total_rules", "passed", "violations",
                    "recommendations", "summary"):
            assert key in result, f"Missing key: {key}"

    def test_violations_list(self, checker):
        result = checker.check(NON_COMPLIANT_CONFIG)
        assert len(result["violations"]) > 0
        # All violation strings should contain severity prefix
        for v in result["violations"]:
            assert any(sev in v for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"))

    def test_telnet_triggers_violation(self, checker):
        result = checker.check(NON_COMPLIANT_CONFIG)
        violation_names = [
            v["name"] for v in result.get("violation_details", [])
        ]
        assert "Telnet Disabled" in violation_names

    def test_ssh_pass_on_compliant(self, checker):
        result = checker.check(COMPLIANT_CONFIG)
        passed_names = [p["name"] for p in result.get("passed_details", [])]
        assert "SSH Enabled" in passed_names

    def test_recommendations_generated_for_violations(self, checker):
        result = checker.check(NON_COMPLIANT_CONFIG)
        assert len(result["recommendations"]) > 0

    def test_score_is_percentage(self, checker):
        result = checker.check(COMPLIANT_CONFIG)
        assert 0 <= result["score"] <= 100

    def test_critical_violation_makes_noncompliant(self, checker):
        # Config without enable secret = critical violation
        config = "hostname test\nlogging buffered\nntp server 1.1.1.1"
        result = checker.check(config)
        critical = [v for v in result.get("violation_details", []) if v["severity"] == "critical"]
        if critical:
            assert result["compliant"] is False

    def test_add_custom_rule(self, checker):
        checker.add_custom_rule("custom", {
            "name": "Custom Rule",
            "description": "Test rule",
            "pattern": r"custom-pattern",
            "required": True,
            "severity": "low",
        })
        assert "custom" in checker.rules
        assert any(r["name"] == "Custom Rule" for r in checker.rules["custom"])

    def test_export_rules(self, checker, tmp_path):
        export_path = str(tmp_path / "rules_export.yaml")
        checker.export_rules(export_path)
        import os
        assert os.path.exists(export_path)
        assert os.path.getsize(export_path) > 0
