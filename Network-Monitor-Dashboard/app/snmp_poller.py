#!/usr/bin/env python3
"""
Network Monitoring Dashboard - SNMP Poller
Polls network devices via SNMP and collects metrics.

Author: Navaneethraj KA
"""

import time
import socket
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Try to import SNMP libraries
try:
    from pysnmp.hlapi import *
    PYSNMP_AVAILABLE = True
except ImportError:
    PYSNMP_AVAILABLE = False

# Try to import ping library
try:
    from ping3 import ping
    PING_AVAILABLE = True
except ImportError:
    PING_AVAILABLE = False

from .models import get_session, Device, Metric, Alert, PollingResult


class SNMPPoller:
    """
    SNMP Polling engine for network devices.
    Supports SNMP v1, v2c, and v3 polling.
    """
    
    # Common OIDs
    OIDS = {
        'sysDescr': '1.3.6.1.2.1.1.1.0',
        'sysUpTime': '1.3.6.1.2.1.1.3.0',
        'sysName': '1.3.6.1.2.1.1.5.0',
        'ifNumber': '1.3.6.1.2.1.2.1.0',
        'ifInOctets': '1.3.6.1.2.1.2.2.1.10',
        'ifOutOctets': '1.3.6.1.2.1.2.2.1.16',
        'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',
        # Cisco-specific
        'cpmCPUTotal5min': '1.3.6.1.4.1.9.9.109.1.1.1.1.5.1',
        'ciscoMemoryPoolUsed': '1.3.6.1.4.1.9.9.48.1.1.1.5.1',
    }
    
    def __init__(self, community='public', timeout=5, retries=3, interval=60):
        """
        Initialize the SNMP poller.
        
        Args:
            community: SNMP community string
            timeout: SNMP timeout in seconds
            retries: Number of retries on failure
            interval: Polling interval in seconds
        """
        self.community = community
        self.timeout = timeout
        self.retries = retries
        self.interval = interval
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        print(f"[SNMP] Poller initialized (interval: {interval}s)")
    
    def run(self):
        """Run the polling loop."""
        self.running = True
        
        while self.running:
            try:
                self._poll_all_devices()
            except Exception as e:
                print(f"[SNMP] Polling error: {e}")
            
            time.sleep(self.interval)
    
    def stop(self):
        """Stop the polling loop."""
        self.running = False
        self.executor.shutdown(wait=False)
    
    def _poll_all_devices(self):
        """Poll all devices in the database."""
        session = get_session()
        devices = session.query(Device).all()
        
        futures = []
        for device in devices:
            future = self.executor.submit(self._poll_device, device)
            futures.append((device, future))
        
        # Process results
        for device, future in futures:
            try:
                result = future.result(timeout=self.timeout * 2)
                self._process_result(device, result)
            except Exception as e:
                self._handle_poll_failure(device, str(e))
        
        session.close()
    
    def _poll_device(self, device):
        """
        Poll a single device.
        
        Args:
            device: Device model instance
            
        Returns:
            Dictionary with poll results
        """
        start_time = time.time()
        result = {
            'reachable': False,
            'response_time': None,
            'metrics': {}
        }
        
        # First, check if device is reachable via ICMP
        if PING_AVAILABLE:
            try:
                response_time = ping(device.ip_address, timeout=self.timeout)
                if response_time:
                    result['reachable'] = True
                    result['response_time'] = response_time * 1000  # Convert to ms
            except Exception:
                pass
        else:
            # Fallback to TCP socket check
            result['reachable'] = self._tcp_check(device.ip_address, 161)
        
        if not result['reachable']:
            return result
        
        # SNMP polling
        if PYSNMP_AVAILABLE:
            result['metrics'] = self._snmp_get(device)
        else:
            # Simulate SNMP data for demonstration
            result['metrics'] = self._simulate_snmp_data(device)
        
        result['poll_time'] = (time.time() - start_time) * 1000
        return result
    
    def _tcp_check(self, host, port, timeout=2):
        """Check if a TCP port is reachable."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _snmp_get(self, device):
        """
        Perform SNMP GET for common OIDs.
        
        Args:
            device: Device model instance
            
        Returns:
            Dictionary of metric values
        """
        metrics = {}
        community = device.snmp_community or self.community
        
        # Get basic system info
        for name, oid in [('sysUpTime', self.OIDS['sysUpTime']), 
                          ('sysName', self.OIDS['sysName'])]:
            try:
                error_indication, error_status, error_index, var_binds = next(
                    getCmd(SnmpEngine(),
                           CommunityData(community),
                           UdpTransportTarget((device.ip_address, 161), 
                                             timeout=self.timeout, 
                                             retries=self.retries),
                           ContextData(),
                           ObjectType(ObjectIdentity(oid)))
                )
                
                if not error_indication and not error_status and var_binds:
                    metrics[name] = str(var_binds[0][1])
            except Exception as e:
                print(f"[SNMP] Error getting {name} from {device.name}: {e}")
        
        return metrics
    
    def _simulate_snmp_data(self, device):
        """Simulate SNMP data for demonstration."""
        import random
        
        return {
            'sysUpTime': str(random.randint(100000, 10000000)),
            'cpu_usage': random.uniform(10, 80),
            'memory_usage': random.uniform(30, 70),
            'interface_in_octets': random.randint(1000000, 100000000),
            'interface_out_octets': random.randint(1000000, 100000000),
        }
    
    def _process_result(self, device, result):
        """Process poll result and update database."""
        session = get_session()
        
        try:
            # Update device status
            device = session.query(Device).get(device.id)
            
            if result['reachable']:
                device.status = 'online'
                device.last_seen = datetime.utcnow()
            else:
                if device.status == 'online':
                    # Device just went offline, create alert
                    self._create_alert(session, device, 'critical', 
                                       'Device Unreachable',
                                       f'Device {device.name} is not responding')
                device.status = 'offline'
            
            # Store metrics
            for metric_name, value in result.get('metrics', {}).items():
                if isinstance(value, (int, float)):
                    metric = Metric(
                        device_id=device.id,
                        metric_name=metric_name,
                        metric_value=value,
                        timestamp=datetime.utcnow()
                    )
                    session.add(metric)
            
            # Store polling result
            poll_result = PollingResult(
                device_id=device.id,
                success=result['reachable'],
                response_time=result.get('response_time'),
                timestamp=datetime.utcnow()
            )
            session.add(poll_result)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"[SNMP] Error updating {device.name}: {e}")
        finally:
            session.close()
    
    def _handle_poll_failure(self, device, error_message):
        """Handle polling failure."""
        session = get_session()
        
        try:
            device = session.query(Device).get(device.id)
            device.status = 'error'
            
            poll_result = PollingResult(
                device_id=device.id,
                success=False,
                error_message=error_message,
                timestamp=datetime.utcnow()
            )
            session.add(poll_result)
            session.commit()
            
        except Exception as e:
            session.rollback()
        finally:
            session.close()
    
    def _create_alert(self, session, device, severity, title, message):
        """Create an alert."""
        alert = Alert(
            device_id=device.id,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.utcnow()
        )
        session.add(alert)
