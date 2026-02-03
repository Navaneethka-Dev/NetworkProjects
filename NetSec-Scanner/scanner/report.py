#!/usr/bin/env python3
"""
Network Security Scanner - Report Generator
Author: Navaneethraj KA
"""

import os
import json
from datetime import datetime
from jinja2 import Template


class ReportGenerator:
    """Generate scan reports in various formats."""
    
    HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><title>Security Scan Report</title>
<style>body{font-family:Arial;margin:40px;background:#1a1a2e;color:#eee}
h1{color:#00d4ff}.critical{color:#ef4444}.high{color:#f59e0b}
.medium{color:#eab308}.low{color:#22c55e}.card{background:#16213e;
padding:20px;border-radius:10px;margin:20px 0}table{width:100%;
border-collapse:collapse}th,td{padding:10px;text-align:left;
border-bottom:1px solid #334}th{color:#00d4ff}</style></head>
<body><h1>🔒 Security Scan Report</h1>
<div class="card"><p>Target: {{ target }}</p><p>Date: {{ date }}</p>
<p>Duration: {{ duration }}s</p></div>
<h2>Open Ports</h2><div class="card"><table><tr><th>Host</th><th>Port</th>
<th>Service</th><th>Version</th></tr>{% for host, ports in ports.items() %}
{% for p in ports %}<tr><td>{{ host }}</td><td>{{ p.port }}</td>
<td>{{ p.service }}</td><td>{{ p.version }}</td></tr>{% endfor %}{% endfor %}
</table></div><h2>Vulnerabilities</h2><div class="card">
{% for v in vulns %}<p class="{{ v.severity }}">
[{{ v.severity|upper }}] {{ v.title }} - {{ v.host }}</p>{% endfor %}
</div></body></html>"""
    
    def generate(self, results: dict, output: str, format: str = 'html'):
        """Generate report."""
        os.makedirs(os.path.dirname(output) or 'reports', exist_ok=True)
        if format == 'json':
            with open(output, 'w') as f:
                json.dump(results, f, indent=2)
        elif format == 'html':
            tmpl = Template(self.HTML_TEMPLATE)
            html = tmpl.render(target=results['target'], 
                              date=results.get('start_time', ''),
                              duration=results.get('duration', 0),
                              ports=results.get('ports', {}),
                              vulns=results.get('vulnerabilities', []))
            with open(output, 'w') as f:
                f.write(html)
        else:
            with open(output, 'w') as f:
                f.write(f"Scan Report: {results['target']}\n{'='*50}\n")
                f.write(json.dumps(results, indent=2))
