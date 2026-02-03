"""
NetAutomate Pro - Device Connectors
Handles SSH connections to network devices using Netmiko.

Author: Navaneethraj KA
"""

import os
from typing import Dict, List, Optional, Any

# Try to import netmiko, provide mock if not available
try:
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False
    
from .utils import setup_logging

logger = setup_logging()


class DeviceConnector:
    """
    Handles connections to network devices.
    Supports Cisco IOS, NX-OS, and Juniper Junos devices.
    """
    
    DEVICE_TYPE_MAP = {
        'cisco_ios': 'cisco_ios',
        'cisco_nxos': 'cisco_nxos',
        'cisco_xe': 'cisco_xe',
        'cisco_xr': 'cisco_xr',
        'juniper': 'juniper_junos',
        'juniper_junos': 'juniper_junos',
        'arista_eos': 'arista_eos',
    }
    
    def __init__(self, device_info: Dict[str, Any]):
        """
        Initialize device connector.
        
        Args:
            device_info: Dictionary containing device connection details
                - hostname: Device hostname
                - ip: Device IP address
                - device_type: Type of device (cisco_ios, juniper, etc.)
                - username: SSH username
                - password: SSH password
                - port: SSH port (optional, default 22)
                - secret: Enable password (optional)
        """
        self.device_info = device_info
        self.hostname = device_info.get('hostname', device_info.get('ip'))
        self.connection = None
        
        # Prepare connection parameters
        self.conn_params = {
            'device_type': self.DEVICE_TYPE_MAP.get(
                device_info.get('device_type', 'cisco_ios'), 
                'cisco_ios'
            ),
            'host': device_info.get('ip', device_info.get('hostname')),
            'username': device_info.get('username', os.getenv('NET_USERNAME', 'admin')),
            'password': device_info.get('password', os.getenv('NET_PASSWORD', '')),
            'port': device_info.get('port', 22),
            'timeout': device_info.get('timeout', 30),
            'session_log': f"logs/{self.hostname}_session.log"
        }
        
        if device_info.get('secret'):
            self.conn_params['secret'] = device_info['secret']
    
    def connect(self) -> bool:
        """
        Establish SSH connection to the device.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not NETMIKO_AVAILABLE:
            logger.warning("Netmiko not installed. Running in simulation mode.")
            return True
            
        try:
            logger.info(f"Connecting to {self.hostname} ({self.conn_params['host']})")
            self.connection = ConnectHandler(**self.conn_params)
            logger.info(f"Connected to {self.hostname}")
            return True
            
        except NetmikoTimeoutException:
            logger.error(f"Connection timeout to {self.hostname}")
            raise ConnectionError(f"Timeout connecting to {self.hostname}")
            
        except NetmikoAuthenticationException:
            logger.error(f"Authentication failed for {self.hostname}")
            raise ConnectionError(f"Authentication failed for {self.hostname}")
            
        except Exception as e:
            logger.error(f"Connection error to {self.hostname}: {str(e)}")
            raise ConnectionError(f"Connection failed: {str(e)}")
    
    def disconnect(self):
        """Close the SSH connection."""
        if self.connection:
            self.connection.disconnect()
            logger.info(f"Disconnected from {self.hostname}")
            self.connection = None
    
    def send_command(self, command: str, timeout: int = 30) -> str:
        """
        Send a show command and return output.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Command output as string
        """
        if not NETMIKO_AVAILABLE:
            return self._simulate_command(command)
            
        if not self.connection:
            self.connect()
        
        try:
            output = self.connection.send_command(
                command,
                read_timeout=timeout
            )
            return output
            
        except Exception as e:
            logger.error(f"Command failed on {self.hostname}: {str(e)}")
            raise
    
    def send_config(self, config_commands: List[str]) -> str:
        """
        Send configuration commands to the device.
        
        Args:
            config_commands: List of configuration commands
            
        Returns:
            Configuration output
        """
        if not NETMIKO_AVAILABLE:
            return self._simulate_config(config_commands)
            
        if not self.connection:
            self.connect()
        
        try:
            output = self.connection.send_config_set(config_commands)
            
            # Save configuration
            self.connection.save_config()
            
            logger.info(f"Configuration applied to {self.hostname}")
            return output
            
        except Exception as e:
            logger.error(f"Configuration failed on {self.hostname}: {str(e)}")
            raise
    
    def get_running_config(self) -> str:
        """
        Get the running configuration.
        
        Returns:
            Running configuration as string
        """
        device_type = self.device_info.get('device_type', 'cisco_ios')
        
        if 'juniper' in device_type:
            command = 'show configuration'
        else:
            command = 'show running-config'
        
        return self.send_command(command, timeout=60)
    
    def get_version(self) -> str:
        """Get device version information."""
        return self.send_command('show version')
    
    def get_interfaces(self) -> str:
        """Get interface status."""
        device_type = self.device_info.get('device_type', 'cisco_ios')
        
        if 'juniper' in device_type:
            command = 'show interfaces terse'
        else:
            command = 'show ip interface brief'
        
        return self.send_command(command)
    
    def _simulate_command(self, command: str) -> str:
        """Simulate command output for testing without actual devices."""
        logger.info(f"[SIMULATION] Executing: {command}")
        
        if 'show version' in command:
            return """
Cisco IOS Software, Version 15.1(4)M4
Router upance: 10 days, 5 hours, 30 minutes
System image file is "flash:c2900-universalk9-mz.SPA.151-4.M4.bin"

Processor board ID FTX1234ABCD
1 Gigabit Ethernet interface
256K bytes of NVRAM
"""
        elif 'show running-config' in command:
            return """
Building configuration...

Current configuration : 1234 bytes
!
version 15.1
service timestamps debug datetime msec
service timestamps log datetime msec
!
hostname Router1
!
enable secret 5 $1$merd$encrypted
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
router ospf 1
 network 192.168.1.0 0.0.0.255 area 0
 network 10.0.0.0 0.0.0.255 area 0
!
line con 0
line vty 0 4
 login local
 transport input ssh
!
end
"""
        elif 'show ip interface brief' in command:
            return """
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.1.1     YES manual up                    up
GigabitEthernet0/1     10.0.0.1        YES manual up                    up
Loopback0              1.1.1.1         YES manual up                    up
"""
        else:
            return f"[SIMULATION] Output for: {command}"
    
    def _simulate_config(self, config_commands: List[str]) -> str:
        """Simulate configuration for testing."""
        logger.info(f"[SIMULATION] Configuring {len(config_commands)} commands")
        output_lines = ["configure terminal"]
        
        for cmd in config_commands:
            output_lines.append(f"Router(config)# {cmd}")
        
        output_lines.append("end")
        output_lines.append("Configuration saved successfully.")
        
        return "\n".join(output_lines)
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
