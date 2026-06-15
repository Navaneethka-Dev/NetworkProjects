"""
Tests for netautomate.reporter — ReportGenerator
"""
import os
import json
import pytest
from netautomate.reporter import ReportGenerator


SAMPLE_COMPLIANCE_RESULTS = [
    {
        "device": "router1",
        "compliant": True,
        "score": 91,
        "total_rules": 11,
        "passed": 10,
        "violations": [],
        "violation_details": [],
        "passed_details": [
            {"name": "SSH Enabled", "category": "security", "severity": "high"},
        ],
        "recommendations": [],
        "summary": "Compliance Status: Excellent (91%)",
    },
    {
        "device": "switch1",
        "compliant": False,
        "score": 45,
        "total_rules": 11,
        "passed": 5,
        "violations": ["CRITICAL: Enable Secret Set - Enable secret should be configured"],
        "violation_details": [
            {"name": "Enable Secret Set", "category": "security", "severity": "critical",
             "description": "Enable secret should be configured"},
        ],
        "passed_details": [],
        "recommendations": ['Set enable secret: "enable secret <password>"'],
        "summary": "Compliance Status: Critical (45%) | 1 Critical Issue(s)",
    },
]

SAMPLE_BACKUP_LIST = [
    {"hostname": "router1", "filename": "router1_20240101_120000.cfg",
     "size": 4096, "modified": "2024-01-01T12:00:00"},
    {"hostname": "switch1", "filename": "switch1_20240101_130000.cfg",
     "size": 2048, "modified": "2024-01-01T13:00:00"},
]


@pytest.fixture
def reporter(tmp_path):
    return ReportGenerator(output_dir=str(tmp_path / "reports"))


def _read(path: str) -> str:
    """Read a file with explicit UTF-8 encoding (required on Windows)."""
    return open(path, encoding="utf-8").read()


class TestReportGenerator:
    # ── HTML compliance report ────────────────────────────────────────────────

    def test_html_compliance_report_created(self, reporter):
        path = reporter.generate_compliance_report(SAMPLE_COMPLIANCE_RESULTS, fmt="html")
        assert os.path.exists(path)
        assert path.endswith(".html")

    def test_html_compliance_report_non_empty(self, reporter):
        path = reporter.generate_compliance_report(SAMPLE_COMPLIANCE_RESULTS, fmt="html")
        content = _read(path)
        assert len(content) > 500

    def test_html_compliance_contains_device_names(self, reporter):
        path = reporter.generate_compliance_report(SAMPLE_COMPLIANCE_RESULTS, fmt="html")
        content = _read(path)
        assert "router1" in content
        assert "switch1" in content

    def test_html_compliance_shows_scores(self, reporter):
        path = reporter.generate_compliance_report(SAMPLE_COMPLIANCE_RESULTS, fmt="html")
        content = _read(path)
        assert "91" in content
        assert "45" in content

    def test_html_compliance_contains_compliant_badge(self, reporter):
        path = reporter.generate_compliance_report(SAMPLE_COMPLIANCE_RESULTS, fmt="html")
        content = _read(path)
        assert "COMPLIANT" in content
        assert "NON-COMPLIANT" in content

    def test_html_compliance_custom_filename(self, reporter):
        path = reporter.generate_compliance_report(
            SAMPLE_COMPLIANCE_RESULTS, fmt="html", filename="my_report"
        )
        assert "my_report.html" in path

    # ── JSON compliance report ────────────────────────────────────────────────

    def test_json_compliance_report_created(self, reporter):
        path = reporter.generate_compliance_report(SAMPLE_COMPLIANCE_RESULTS, fmt="json")
        assert path.endswith(".json")
        assert os.path.exists(path)

    def test_json_compliance_valid_json(self, reporter):
        path = reporter.generate_compliance_report(SAMPLE_COMPLIANCE_RESULTS, fmt="json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["report_type"] == "compliance"
        assert len(data["results"]) == 2

    # ── HTML backup report ────────────────────────────────────────────────────

    def test_html_backup_report_created(self, reporter):
        path = reporter.generate_backup_report(SAMPLE_BACKUP_LIST, fmt="html")
        assert os.path.exists(path)
        assert path.endswith(".html")

    def test_html_backup_contains_hostnames(self, reporter):
        path = reporter.generate_backup_report(SAMPLE_BACKUP_LIST, fmt="html")
        content = _read(path)
        assert "router1" in content
        assert "switch1" in content

    def test_html_backup_contains_filenames(self, reporter):
        path = reporter.generate_backup_report(SAMPLE_BACKUP_LIST, fmt="html")
        content = _read(path)
        assert "router1_20240101_120000.cfg" in content

    # ── JSON backup report ────────────────────────────────────────────────────

    def test_json_backup_report_valid(self, reporter):
        path = reporter.generate_backup_report(SAMPLE_BACKUP_LIST, fmt="json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["report_type"] == "backup"
        assert len(data["backups"]) == 2
