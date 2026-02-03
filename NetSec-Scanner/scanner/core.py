#!/usr/bin/env python3
"""
Network Security Scanner - Core Scanner Engine
Main scanner class orchestrating all scanning operations.

Author: Navaneethraj KA
"""

import socket
import ipaddress
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Any, Optional

from .port_scanner import PortScanner
from .host_discovery import HostDiscovery
from .vuln_scanner import VulnerabilityScanner


class SecurityScanner:
    """
    Main security scanner class.
    Orchestrates port scanning, host discovery, and vulnerability detection.
    """
    
    # Common ports for quick scan
    QUICK_PORTS = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 
                   993, 995, 1723, 3306, 3389, 5900, 8080, 8443]
    
    def __init__(self, threads: int = 100, timeout: float = 2.0, verbose: bool = False):
        """
        Initialize the security scanner.
        
        Args:
            threads: Number of concurrent threads
            timeout: Connection timeout in seconds
            verbose: Enable verbose output
        """
        self.threads = threads
        self.timeout = timeout
        self.verbose = verbose
        
        # Initialize sub-scanners
        self.port_scanner = PortScanner(threads=threads, timeout=timeout)
        self.host_discovery = HostDiscovery(timeout=timeout)
        self.vuln_scanner = VulnerabilityScanner()
        
        if verbose:
            print(f"[DEBUG] Scanner initialized with {threads} threads")
    
    def scan(self, target: str, ports: str = '1-1000', scan_type: str = 'normal',
             include_udp: bool = False, ssl_check: bool = False, 
             web_check: bool = False) -> Dict[str, Any]:
        """
        Perform a security scan on the target.
        
        Args:
            target: Target IP, hostname, or CIDR range
            ports: Port range to scan (e.g., '1-1000' or '22,80,443')
            scan_type: Scan type ('quick', 'normal', 'full')
            include_udp: Include UDP port scanning
            ssl_check: Perform SSL/TLS analysis
            web_check: Perform web vulnerability checks
            
        Returns:
            Dictionary containing scan results
        """
        start_time = time.time()
        
        results = {
            'target': target,
            'scan_type': scan_type,
            'start_time': datetime.now().isoformat(),
            'hosts': [],
            'ports': {},
            'vulnerabilities': [],
            'ssl_issues': [],
            'web_vulnerabilities': []
        }
        
        # Parse targets
        targets = self._parse_targets(target)
        
        if self.verbose:
            print(f"[DEBUG] Scanning {len(targets)} target(s)")
        
        # Step 1: Host Discovery
        print(f"[*] Discovering hosts...")
        results['hosts'] = self.host_discovery.discover(targets)
        live_hosts = [h['ip'] for h in results['hosts'] if h['status'] == 'up']
        print(f"[+] Found {len(live_hosts)} live host(s)")
        
        if not live_hosts:
            results['duration'] = time.time() - start_time
            return results
        
        # Step 2: Port Scanning
        print(f"[*] Scanning ports...")
        port_list = self._parse_ports(ports, scan_type)
        
        for host in live_hosts:
            open_ports = self.port_scanner.scan(host, port_list, include_udp)
            if open_ports:
                results['ports'][host] = open_ports
                print(f"[+] {host}: {len(open_ports)} open port(s)")
        
        # Step 3: Vulnerability Scanning (if full scan)
        if scan_type == 'full':
            print(f"[*] Checking for vulnerabilities...")
            for host, ports in results['ports'].items():
                vulns = self.vuln_scanner.scan(host, ports)
                results['vulnerabilities'].extend(vulns)
            
            if results['vulnerabilities']:
                print(f"[!] Found {len(results['vulnerabilities'])} vulnerability/ies")
        
        # Step 4: SSL/TLS Check
        if ssl_check:
            print(f"[*] Analyzing SSL/TLS...")
            for host, ports in results['ports'].items():
                ssl_ports = [p for p in ports if p['port'] in [443, 8443, 993, 995]]
                for port in ssl_ports:
                    ssl_issues = self._check_ssl(host, port['port'])
                    results['ssl_issues'].extend(ssl_issues)
        
        # Step 5: Web Vulnerability Check
        if web_check:
            print(f"[*] Checking web vulnerabilities...")
            for host, ports in results['ports'].items():
                web_ports = [p for p in ports if p['port'] in [80, 443, 8080, 8443]]
                for port in web_ports:
                    web_vulns = self._check_web(host, port['port'])
                    results['web_vulnerabilities'].extend(web_vulns)
        
        results['duration'] = time.time() - start_time
        results['end_time'] = datetime.now().isoformat()
        
        return results
    
    def _parse_targets(self, target: str) -> List[str]:
        """Parse target string into list of IP addresses."""
        targets = []
        
        try:
            # Check if it's a CIDR range
            if '/' in target:
                network = ipaddress.ip_network(target, strict=False)
                targets = [str(ip) for ip in network.hosts()]
            else:
                # Single host - resolve hostname if needed
                try:
                    ip = socket.gethostbyname(target)
                    targets = [ip]
                except socket.gaierror:
                    targets = [target]
        except ValueError:
            targets = [target]
        
        return targets
    
    def _parse_ports(self, ports: str, scan_type: str) -> List[int]:
        """Parse port string into list of port numbers."""
        if scan_type == 'quick':
            return self.QUICK_PORTS
        
        if scan_type == 'full':
            return list(range(1, 65536))
        
        port_list = []
        
        for part in ports.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                port_list.extend(range(int(start), int(end) + 1))
            else:
                port_list.append(int(part))
        
        return port_list
    
    def _check_ssl(self, host: str, port: int) -> List[Dict]:
        """Check SSL/TLS configuration."""
        issues = []
        
        try:
            import ssl
            import socket
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    version = ssock.version()
                    cipher = ssock.cipher()
                    
                    # Check for weak TLS versions
                    if version in ['TLSv1', 'TLSv1.1', 'SSLv3']:
                        issues.append({
                            'host': host,
                            'port': port,
                            'severity': 'medium',
                            'title': f'Weak TLS Version: {version}',
                            'description': f'Server supports outdated {version}'
                        })
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] SSL check error for {host}:{port}: {e}")
        
        return issues
    
    def _check_web(self, host: str, port: int) -> List[Dict]:
        """Basic web vulnerability checks."""
        vulnerabilities = []
        
        try:
            import requests
            
            protocol = 'https' if port in [443, 8443] else 'http'
            base_url = f"{protocol}://{host}:{port}"
            
            # Check server header disclosure
            response = requests.get(base_url, timeout=self.timeout, verify=False)
            server = response.headers.get('Server', '')
            
            if server:
                vulnerabilities.append({
                    'host': host,
                    'port': port,
                    'severity': 'info',
                    'title': 'Server Version Disclosure',
                    'description': f'Server header reveals: {server}'
                })
            
            # Check for common sensitive paths
            sensitive_paths = ['/admin', '/.git', '/.env', '/backup', '/phpinfo.php']
            for path in sensitive_paths:
                try:
                    resp = requests.get(f"{base_url}{path}", timeout=self.timeout, verify=False)
                    if resp.status_code == 200:
                        vulnerabilities.append({
                            'host': host,
                            'port': port,
                            'severity': 'medium',
                            'title': f'Sensitive Path Accessible: {path}',
                            'description': f'Path {path} is accessible'
                        })
                except:
                    pass
                    
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] Web check error for {host}:{port}: {e}")
        
        return vulnerabilities
