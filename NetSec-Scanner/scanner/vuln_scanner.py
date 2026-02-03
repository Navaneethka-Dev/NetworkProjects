#!/usr/bin/env python3
"""
Network Security Scanner - Vulnerability Scanner
Author: Navaneethraj KA
"""

import re
from typing import List, Dict


class VulnerabilityScanner:
    """Vulnerability scanner checking for known CVEs."""
    
    VULN_DATABASE = [
        {'cve': 'CVE-2021-44228', 'name': 'Log4j RCE', 'severity': 'critical', 
         'services': ['java'], 'pattern': r'log4j.*2\.[0-9]'},
        {'cve': 'CVE-2017-0144', 'name': 'EternalBlue', 'severity': 'critical',
         'services': ['smb'], 'pattern': r'SMBv1'},
        {'cve': 'CVE-2014-0160', 'name': 'Heartbleed', 'severity': 'high',
         'services': ['ssl'], 'pattern': r'OpenSSL/1\.0\.1[a-f]'},
    ]
    
    def scan(self, host: str, ports: List[Dict]) -> List[Dict]:
        """Scan for vulnerabilities."""
        vulns = []
        for port in ports:
            svc = port.get('service', '').lower()
            ver = port.get('version', '')
            for v in self.VULN_DATABASE:
                if any(s in svc for s in v['services']):
                    if v['pattern'] and re.search(v['pattern'], ver, re.I):
                        vulns.append({'host': host, 'port': port['port'],
                                     'cve': v['cve'], 'title': v['name'],
                                     'severity': v['severity']})
        return vulns
