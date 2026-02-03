#!/usr/bin/env python3
"""
Network Security Scanner - Port Scanner
TCP and UDP port scanning functionality.

Author: Navaneethraj KA
"""

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional


class PortScanner:
    """
    TCP/UDP port scanner with service detection.
    """
    
    # Common service banners
    SERVICE_PROBES = {
        21: (b'', 'FTP'),
        22: (b'', 'SSH'),
        23: (b'', 'Telnet'),
        25: (b'EHLO test\r\n', 'SMTP'),
        80: (b'HEAD / HTTP/1.0\r\n\r\n', 'HTTP'),
        110: (b'', 'POP3'),
        143: (b'', 'IMAP'),
        443: (b'', 'HTTPS'),
        3306: (b'', 'MySQL'),
        3389: (b'', 'RDP'),
        5432: (b'', 'PostgreSQL'),
        6379: (b'PING\r\n', 'Redis'),
        27017: (b'', 'MongoDB'),
    }
    
    COMMON_SERVICES = {
        21: 'ftp', 22: 'ssh', 23: 'telnet', 25: 'smtp', 53: 'dns',
        80: 'http', 110: 'pop3', 111: 'rpcbind', 135: 'msrpc',
        139: 'netbios-ssn', 143: 'imap', 443: 'https', 445: 'microsoft-ds',
        993: 'imaps', 995: 'pop3s', 1433: 'mssql', 1521: 'oracle',
        3306: 'mysql', 3389: 'ms-wbt-server', 5432: 'postgresql',
        5900: 'vnc', 6379: 'redis', 8080: 'http-proxy', 8443: 'https-alt',
        27017: 'mongodb'
    }
    
    def __init__(self, threads: int = 100, timeout: float = 2.0):
        """
        Initialize the port scanner.
        
        Args:
            threads: Number of concurrent threads
            timeout: Connection timeout in seconds
        """
        self.threads = threads
        self.timeout = timeout
    
    def scan(self, host: str, ports: List[int], 
             include_udp: bool = False) -> List[Dict]:
        """
        Scan specified ports on a host.
        
        Args:
            host: Target IP address
            ports: List of ports to scan
            include_udp: Include UDP scanning
            
        Returns:
            List of open ports with details
        """
        open_ports = []
        
        # TCP scan
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self._scan_tcp_port, host, port): port 
                for port in ports
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    open_ports.append(result)
        
        # UDP scan (if enabled)
        if include_udp:
            udp_results = self._scan_udp_ports(host, ports)
            open_ports.extend(udp_results)
        
        # Sort by port number
        open_ports.sort(key=lambda x: x['port'])
        
        return open_ports
    
    def _scan_tcp_port(self, host: str, port: int) -> Optional[Dict]:
        """
        Scan a single TCP port.
        
        Args:
            host: Target IP address
            port: Port number
            
        Returns:
            Port details if open, None if closed
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            result = sock.connect_ex((host, port))
            
            if result == 0:
                # Port is open
                service = self.COMMON_SERVICES.get(port, 'unknown')
                version = self._grab_banner(sock, host, port)
                
                sock.close()
                
                return {
                    'port': port,
                    'protocol': 'tcp',
                    'state': 'open',
                    'service': service,
                    'version': version
                }
            
            sock.close()
            return None
            
        except (socket.timeout, socket.error):
            return None
    
    def _grab_banner(self, sock: socket.socket, host: str, port: int) -> str:
        """
        Attempt to grab service banner.
        
        Args:
            sock: Connected socket
            host: Target host
            port: Port number
            
        Returns:
            Service banner/version string
        """
        try:
            # Send probe if available
            probe, _ = self.SERVICE_PROBES.get(port, (b'', ''))
            
            if probe:
                sock.send(probe)
            
            sock.settimeout(2)
            banner = sock.recv(1024)
            
            if banner:
                # Clean up banner
                banner_str = banner.decode('utf-8', errors='ignore').strip()
                # Take first line only
                banner_str = banner_str.split('\n')[0][:100]
                return banner_str
                
        except:
            pass
        
        return ''
    
    def _scan_udp_ports(self, host: str, ports: List[int]) -> List[Dict]:
        """
        Scan UDP ports (limited accuracy).
        
        Args:
            host: Target IP address
            ports: List of ports to scan
            
        Returns:
            List of potentially open UDP ports
        """
        open_ports = []
        
        # Only scan common UDP ports
        common_udp = [53, 67, 68, 69, 123, 137, 138, 161, 162, 500, 514, 520]
        udp_ports = [p for p in ports if p in common_udp]
        
        for port in udp_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(self.timeout)
                
                # Send empty packet
                sock.sendto(b'', (host, port))
                
                try:
                    data, _ = sock.recvfrom(1024)
                    # Got response - port is open
                    open_ports.append({
                        'port': port,
                        'protocol': 'udp',
                        'state': 'open',
                        'service': self._get_udp_service(port),
                        'version': ''
                    })
                except socket.timeout:
                    # No response - could be open or filtered
                    pass
                    
                sock.close()
                
            except:
                pass
        
        return open_ports
    
    def _get_udp_service(self, port: int) -> str:
        """Get UDP service name for port."""
        udp_services = {
            53: 'dns', 67: 'dhcp', 68: 'dhcp', 69: 'tftp',
            123: 'ntp', 137: 'netbios-ns', 138: 'netbios-dgm',
            161: 'snmp', 162: 'snmptrap', 500: 'isakmp',
            514: 'syslog', 520: 'rip'
        }
        return udp_services.get(port, 'unknown')
