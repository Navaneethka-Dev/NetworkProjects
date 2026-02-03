#!/usr/bin/env python3
"""
Network Security Scanner - Host Discovery
Network host discovery and ping scanning.

Author: Navaneethraj KA
"""

import socket
import struct
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

# Try to import ping library
try:
    from ping3 import ping
    PING_AVAILABLE = True
except ImportError:
    PING_AVAILABLE = False


class HostDiscovery:
    """
    Network host discovery using various techniques.
    """
    
    def __init__(self, timeout: float = 2.0, threads: int = 50):
        """
        Initialize host discovery.
        
        Args:
            timeout: Ping timeout in seconds
            threads: Number of concurrent threads
        """
        self.timeout = timeout
        self.threads = threads
    
    def discover(self, targets: List[str]) -> List[Dict]:
        """
        Discover live hosts in target list.
        
        Args:
            targets: List of IP addresses to check
            
        Returns:
            List of host information dictionaries
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self._check_host, ip): ip 
                for ip in targets
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        return results
    
    def _check_host(self, ip: str) -> Dict:
        """
        Check if a host is alive.
        
        Args:
            ip: IP address to check
            
        Returns:
            Host information dictionary
        """
        result = {
            'ip': ip,
            'status': 'down',
            'response_time': None,
            'hostname': None,
            'os': None
        }
        
        # Try ICMP ping first
        if PING_AVAILABLE:
            try:
                response_time = ping(ip, timeout=self.timeout)
                if response_time is not None:
                    result['status'] = 'up'
                    result['response_time'] = response_time * 1000  # Convert to ms
            except:
                pass
        
        # If ping fails, try TCP connect to common ports
        if result['status'] == 'down':
            common_ports = [80, 443, 22, 445, 139, 21, 23]
            for port in common_ports:
                if self._tcp_ping(ip, port):
                    result['status'] = 'up'
                    break
        
        # If host is up, try to get more info
        if result['status'] == 'up':
            result['hostname'] = self._resolve_hostname(ip)
            result['os'] = self._fingerprint_os(ip)
        
        return result
    
    def _tcp_ping(self, ip: str, port: int) -> bool:
        """
        Check if a TCP port is reachable.
        
        Args:
            ip: IP address
            port: Port number
            
        Returns:
            True if port is reachable
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _resolve_hostname(self, ip: str) -> str:
        """
        Attempt to resolve IP to hostname.
        
        Args:
            ip: IP address
            
        Returns:
            Hostname or None
        """
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except:
            return None
    
    def _fingerprint_os(self, ip: str) -> str:
        """
        Basic OS fingerprinting based on open ports and banners.
        
        Args:
            ip: IP address
            
        Returns:
            OS guess or None
        """
        os_indicators = []
        
        # Check for Windows-specific ports
        if self._tcp_ping(ip, 445) or self._tcp_ping(ip, 139):
            os_indicators.append('Windows')
        
        # Check for SSH (usually Linux)
        if self._tcp_ping(ip, 22):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((ip, 22))
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                sock.close()
                
                if 'Ubuntu' in banner:
                    return 'Linux (Ubuntu)'
                elif 'Debian' in banner:
                    return 'Linux (Debian)'
                elif banner:
                    os_indicators.append('Linux')
            except:
                pass
        
        # Check for RDP (Windows)
        if self._tcp_ping(ip, 3389):
            return 'Windows'
        
        if os_indicators:
            return os_indicators[0]
        
        return None
    
    def arp_scan(self, network: str) -> List[Dict]:
        """
        Perform ARP scan on local network (requires root/admin).
        
        Args:
            network: Network in CIDR notation
            
        Returns:
            List of discovered hosts with MAC addresses
        """
        results = []
        
        try:
            from scapy.all import ARP, Ether, srp
            
            arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network)
            answered, _ = srp(arp_request, timeout=2, verbose=False)
            
            for sent, received in answered:
                results.append({
                    'ip': received.psrc,
                    'mac': received.hwsrc,
                    'status': 'up'
                })
                
        except ImportError:
            print("[!] Scapy not installed. ARP scan not available.")
        except Exception as e:
            print(f"[!] ARP scan error: {e}")
        
        return results
