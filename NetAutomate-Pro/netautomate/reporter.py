"""
NetAutomate Pro - Report Generator
Generates HTML and JSON compliance/audit reports from check results.

Author: Navaneethraj KA
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils import setup_logging

logger = setup_logging()

# ---------------------------------------------------------------------------
# HTML report template (self-contained, no external CDN dependencies)
# ---------------------------------------------------------------------------
_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NetAutomate Pro – {report_title}</title>
  <style>
    :root {{
      --bg: #0d1117;
      --surface: #161b22;
      --border: #30363d;
      --accent: #238636;
      --accent-warn: #d29922;
      --accent-err: #da3633;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --green: #3fb950;
      --yellow: #e3b341;
      --red: #f85149;
      --blue: #58a6ff;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
      background: var(--bg);
      color: var(--text);
      padding: 2rem;
      line-height: 1.6;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 2rem;
    }}
    header h1 {{ font-size: 1.6rem; color: var(--blue); }}
    header small {{ color: var(--text-muted); font-size: 0.85rem; }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.2rem;
      text-align: center;
    }}
    .card .value {{ font-size: 2.2rem; font-weight: 700; }}
    .card .label {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }}
    .card.green .value {{ color: var(--green); }}
    .card.yellow .value {{ color: var(--yellow); }}
    .card.red .value {{ color: var(--red); }}
    .card.blue .value {{ color: var(--blue); }}
    .section {{ margin-bottom: 2rem; }}
    .section h2 {{
      font-size: 1.1rem;
      color: var(--blue);
      margin-bottom: 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--border);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      background: var(--surface);
      border-radius: 8px;
      overflow: hidden;
    }}
    th {{
      background: #1c2128;
      color: var(--text-muted);
      padding: 0.7rem 1rem;
      text-align: left;
      font-weight: 600;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    td {{
      padding: 0.65rem 1rem;
      border-top: 1px solid var(--border);
      vertical-align: middle;
    }}
    tr:hover td {{ background: rgba(88, 166, 255, 0.04); }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
    }}
    .badge-pass {{ background: rgba(63,185,80,.15); color: var(--green); }}
    .badge-fail {{ background: rgba(248,81,73,.15); color: var(--red); }}
    .badge-warn {{ background: rgba(227,179,65,.15); color: var(--yellow); }}
    .badge-info {{ background: rgba(88,166,255,.15); color: var(--blue); }}
    .sev-critical {{ color: #ff4d4f; font-weight: 700; }}
    .sev-high {{ color: var(--red); }}
    .sev-medium {{ color: var(--yellow); }}
    .sev-low {{ color: var(--green); }}
    footer {{
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border);
      font-size: 0.8rem;
      color: var(--text-muted);
      text-align: center;
    }}
    .progress-bar-wrap {{
      background: #1c2128;
      border-radius: 4px;
      height: 10px;
      width: 100%;
      overflow: hidden;
      margin: 4px 0;
    }}
    .progress-bar {{
      height: 100%;
      border-radius: 4px;
      transition: width 0.4s ease;
    }}
    .bar-green {{ background: var(--green); }}
    .bar-yellow {{ background: var(--yellow); }}
    .bar-red {{ background: var(--red); }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>🌐 NetAutomate Pro</h1>
      <small>{report_title}</small>
    </div>
    <small>Generated: {generated_at}</small>
  </header>

  <!-- Fleet Summary -->
  <div class="summary-grid">
    {summary_cards}
  </div>

  <!-- Per-Device Results -->
  {device_sections}

  <footer>
    NetAutomate Pro v1.0 &nbsp;|&nbsp; Author: Navaneethraj KA &nbsp;|&nbsp;
    github.com/Navaneethka-Dev
  </footer>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Reporter class
# ---------------------------------------------------------------------------

class ReportGenerator:
    """
    Generates compliance and backup reports in HTML and JSON formats.

    Example::

        reporter = ReportGenerator(output_dir="reports")
        reporter.generate_compliance_report(results, fmt="html")
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ReportGenerator initialised. Output dir: {self.output_dir}")

    # ------------------------------------------------------------------
    # Compliance reports
    # ------------------------------------------------------------------

    def generate_compliance_report(
        self,
        results: List[Dict[str, Any]],
        fmt: str = "html",
        filename: Optional[str] = None,
    ) -> str:
        """Generate a compliance report from a list of check results.

        Args:
            results: List returned by
                :py:meth:`~netautomate.core.NetworkAutomation.check_compliance_all`.
            fmt: ``"html"`` or ``"json"``.
            filename: Custom output filename (without extension).

        Returns:
            Absolute path to the generated report file.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = filename or f"compliance_report_{ts}"

        if fmt == "json":
            return self._write_json(
                base,
                {
                    "report_type": "compliance",
                    "generated_at": datetime.now().isoformat(),
                    "results": results,
                },
            )

        return self._build_compliance_html(results, base)

    def generate_backup_report(
        self,
        backup_list: List[Dict[str, Any]],
        fmt: str = "html",
        filename: Optional[str] = None,
    ) -> str:
        """Generate a backup status report.

        Args:
            backup_list: List of backup info dicts (from
                :py:meth:`~netautomate.backup.BackupManager.list_backups`).
            fmt: ``"html"`` or ``"json"``.
            filename: Custom output filename (without extension).

        Returns:
            Absolute path to the generated report file.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = filename or f"backup_report_{ts}"

        if fmt == "json":
            return self._write_json(
                base,
                {
                    "report_type": "backup",
                    "generated_at": datetime.now().isoformat(),
                    "backups": backup_list,
                },
            )

        return self._build_backup_html(backup_list, base)

    # ------------------------------------------------------------------
    # HTML builders
    # ------------------------------------------------------------------

    def _build_compliance_html(self, results: List[Dict], base: str) -> str:
        total_devices = len(results)
        compliant = sum(1 for r in results if r.get("compliant"))
        non_compliant = total_devices - compliant
        avg_score = (
            int(sum(r.get("score", 0) for r in results) / total_devices)
            if total_devices
            else 0
        )
        score_class = (
            "green" if avg_score >= 80 else "yellow" if avg_score >= 60 else "red"
        )

        summary_cards = (
            f'<div class="card blue"><div class="value">{total_devices}</div>'
            f'<div class="label">Devices Checked</div></div>'
            f'<div class="card green"><div class="value">{compliant}</div>'
            f'<div class="label">Compliant</div></div>'
            f'<div class="card red"><div class="value">{non_compliant}</div>'
            f'<div class="label">Non-Compliant</div></div>'
            f'<div class="card {score_class}"><div class="value">{avg_score}%</div>'
            f'<div class="label">Avg Score</div></div>'
        )

        device_sections = ""
        for r in results:
            device_sections += self._device_compliance_section(r)

        html = _HTML_TEMPLATE.format(
            report_title="Compliance Report",
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary_cards=summary_cards,
            device_sections=device_sections,
        )
        return self._write_html(base, html)

    def _device_compliance_section(self, result: Dict) -> str:
        device = result.get("device", "Unknown")
        score = result.get("score", 0)
        compliant = result.get("compliant", False)
        violations = result.get("violation_details", [])
        passed_details = result.get("passed_details", [])
        recommendations = result.get("recommendations", [])
        summary_text = result.get("summary", "")

        bar_class = "bar-green" if score >= 80 else "bar-yellow" if score >= 60 else "bar-red"
        badge = (
            '<span class="badge badge-pass">COMPLIANT</span>'
            if compliant
            else '<span class="badge badge-fail">NON-COMPLIANT</span>'
        )

        rows = ""
        for v in violations:
            sev = v.get("severity", "medium")
            rows += (
                f"<tr><td>{v.get('name','')}</td>"
                f"<td>{v.get('category','')}</td>"
                f"<td class='sev-{sev}'>{sev.upper()}</td>"
                f"<td><span class='badge badge-fail'>FAIL</span></td></tr>"
            )
        for p in passed_details:
            sev = p.get("severity", "low")
            rows += (
                f"<tr><td>{p.get('name','')}</td>"
                f"<td>{p.get('category','')}</td>"
                f"<td class='sev-{sev}'>{sev.upper()}</td>"
                f"<td><span class='badge badge-pass'>PASS</span></td></tr>"
            )

        rec_html = ""
        if recommendations:
            items = "".join(f"<li>{rec}</li>" for rec in recommendations)
            rec_html = f"<ul style='margin:0.5rem 0 0 1.2rem;font-size:0.85rem;color:#8b949e'>{items}</ul>"

        return f"""
<div class="section">
  <h2>🖥 {device} &nbsp; {badge} &nbsp;
      <span style="font-size:0.9rem;color:var(--text-muted)">{summary_text}</span>
  </h2>
  <div class="progress-bar-wrap">
    <div class="progress-bar {bar_class}" style="width:{score}%"></div>
  </div>
  <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:0.8rem">
    Compliance score: {score}%
  </p>
  <table>
    <thead><tr><th>Rule</th><th>Category</th><th>Severity</th><th>Status</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  {rec_html}
</div>
"""

    def _build_backup_html(self, backup_list: List[Dict], base: str) -> str:
        total = len(backup_list)
        total_size = sum(b.get("size", 0) for b in backup_list)
        hosts = len({b.get("hostname", "?") for b in backup_list})

        def _fmt_bytes(n: int) -> str:
            for unit in ("B", "KB", "MB", "GB"):
                if n < 1024:
                    return f"{n:.1f} {unit}"
                n /= 1024
            return f"{n:.1f} TB"

        summary_cards = (
            f'<div class="card blue"><div class="value">{total}</div>'
            f'<div class="label">Total Backups</div></div>'
            f'<div class="card green"><div class="value">{hosts}</div>'
            f'<div class="label">Devices</div></div>'
            f'<div class="card yellow"><div class="value">{_fmt_bytes(total_size)}</div>'
            f'<div class="label">Total Size</div></div>'
        )

        rows = ""
        for b in backup_list:
            rows += (
                f"<tr>"
                f"<td>{b.get('hostname','?')}</td>"
                f"<td style='font-family:monospace;font-size:0.82rem'>{b.get('filename','')}</td>"
                f"<td>{_fmt_bytes(b.get('size', 0))}</td>"
                f"<td>{b.get('modified','')}</td>"
                f"</tr>"
            )

        device_sections = f"""
<div class="section">
  <h2>📦 Backup Inventory</h2>
  <table>
    <thead>
      <tr><th>Device</th><th>Filename</th><th>Size</th><th>Date</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>
"""

        html = _HTML_TEMPLATE.format(
            report_title="Backup Report",
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary_cards=summary_cards,
            device_sections=device_sections,
        )
        return self._write_html(base, html)

    # ------------------------------------------------------------------
    # File writers
    # ------------------------------------------------------------------

    def _write_html(self, base: str, html: str) -> str:
        path = self.output_dir / f"{base}.html"
        path.write_text(html, encoding="utf-8")
        logger.info(f"HTML report written: {path}")
        return str(path)

    def _write_json(self, base: str, data: Dict) -> str:
        path = self.output_dir / f"{base}.json"
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info(f"JSON report written: {path}")
        return str(path)
