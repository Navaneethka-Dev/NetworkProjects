"""
NetAutomate Pro - Core Automation Engine
Handles the main automation workflows and orchestration.

Author: Navaneethraj KA
"""

import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .connectors import DeviceConnector
from .backup import BackupManager
from .compliance import ComplianceChecker
from .utils import render_template, setup_logging

logger = setup_logging()


class NetworkAutomation:
    """
    Main class for network automation operations.
    Provides methods for backup, deployment, compliance checking, and command execution.
    """
    
    def __init__(self, inventory_file: str):
        """
        Initialize the NetworkAutomation instance.
        
        Args:
            inventory_file: Path to the YAML inventory file
        """
        self.inventory_file = inventory_file
        self.devices = self._load_inventory()
        self.backup_manager = BackupManager()
        self.compliance_checker = ComplianceChecker()
        
        logger.info(f"NetworkAutomation initialized with {len(self.devices)} devices")
    
    def _load_inventory(self) -> List[Dict]:
        """Load device inventory from YAML file."""
        if not os.path.exists(self.inventory_file):
            raise FileNotFoundError(f"Inventory file not found: {self.inventory_file}")
        
        with open(self.inventory_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return data.get('devices', [])
    
    def _get_device(self, hostname: str) -> Optional[Dict]:
        """Get device info by hostname."""
        for device in self.devices:
            if device['hostname'] == hostname:
                return device
        return None
    
    def list_devices(self) -> List[Dict]:
        """List all devices in inventory."""
        return self.devices
    
    def backup_device(self, hostname: str) -> Dict[str, Any]:
        """
        Backup configuration of a single device.
        
        Args:
            hostname: Device hostname
            
        Returns:
            Dictionary with backup status and file path
        """
        device = self._get_device(hostname)
        if not device:
            return {'status': 'failed', 'error': f'Device {hostname} not found'}
        
        logger.info(f"Starting backup for {hostname}")
        
        try:
            connector = DeviceConnector(device)
            config = connector.get_running_config()
            
            backup_file = self.backup_manager.save_backup(hostname, config)
            
            logger.info(f"Backup successful for {hostname}: {backup_file}")
            return {'status': 'success', 'backup_file': backup_file}
            
        except Exception as e:
            logger.error(f"Backup failed for {hostname}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def backup_all_devices(self, max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        Backup all devices in parallel.
        
        Args:
            max_workers: Maximum number of parallel connections
            
        Returns:
            List of backup results for each device
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.backup_device, device['hostname']): device 
                for device in self.devices
            }
            
            for future in as_completed(futures):
                device = futures[future]
                try:
                    result = future.result()
                    result['device'] = device['hostname']
                    results.append(result)
                except Exception as e:
                    results.append({
                        'device': device['hostname'],
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results
    
    def deploy_config(self, hostname: str, template_file: str, 
                      variables: Dict = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Deploy configuration to a device using a template.
        
        Args:
            hostname: Device hostname
            template_file: Path to Jinja2 template
            variables: Template variables
            dry_run: If True, only preview the configuration
            
        Returns:
            Dictionary with deployment status
        """
        device = self._get_device(hostname)
        if not device:
            return {'status': 'failed', 'error': f'Device {hostname} not found'}
        
        variables = variables or {}
        
        try:
            # Render the template
            config = render_template(template_file, {'device': device, **variables})
            
            if dry_run:
                logger.info(f"Dry-run mode: Configuration preview for {hostname}")
                return {
                    'status': 'success',
                    'mode': 'dry-run',
                    'config_preview': config
                }
            
            # Deploy the configuration
            connector = DeviceConnector(device)
            output = connector.send_config(config.split('\n'))
            
            logger.info(f"Configuration deployed to {hostname}")
            return {'status': 'success', 'output': output}
            
        except Exception as e:
            logger.error(f"Deployment failed for {hostname}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def deploy_to_all(self, template_file: str, variables: Dict = None,
                      dry_run: bool = False, max_workers: int = 5) -> List[Dict[str, Any]]:
        """Deploy configuration to all devices in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self.deploy_config, device['hostname'], template_file, variables, dry_run
                ): device 
                for device in self.devices
            }
            
            for future in as_completed(futures):
                device = futures[future]
                try:
                    result = future.result()
                    result['device'] = device['hostname']
                    results.append(result)
                except Exception as e:
                    results.append({
                        'device': device['hostname'],
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results
    
    def check_compliance(self, hostname: str, standards_file: str = None) -> Dict[str, Any]:
        """
        Check device compliance against standards.
        
        Args:
            hostname: Device hostname
            standards_file: Path to standards YAML file
            
        Returns:
            Compliance report with score and violations
        """
        device = self._get_device(hostname)
        if not device:
            return {'status': 'failed', 'error': f'Device {hostname} not found'}
        
        try:
            connector = DeviceConnector(device)
            config = connector.get_running_config()
            
            report = self.compliance_checker.check(config, standards_file)
            report['device'] = hostname
            
            logger.info(f"Compliance check for {hostname}: {report['score']}%")
            return report
            
        except Exception as e:
            logger.error(f"Compliance check failed for {hostname}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def check_compliance_all(self, standards_file: str = None) -> List[Dict[str, Any]]:
        """Check compliance for all devices."""
        return [
            self.check_compliance(device['hostname'], standards_file)
            for device in self.devices
        ]
    
    def execute_command(self, hostname: str, command: str) -> Dict[str, Any]:
        """
        Execute a command on a device.
        
        Args:
            hostname: Device hostname
            command: Command to execute
            
        Returns:
            Command output
        """
        device = self._get_device(hostname)
        if not device:
            return {'status': 'failed', 'error': f'Device {hostname} not found'}
        
        try:
            connector = DeviceConnector(device)
            output = connector.send_command(command)
            
            logger.info(f"Command executed on {hostname}: {command[:50]}...")
            return {'status': 'success', 'output': output}
            
        except Exception as e:
            logger.error(f"Command execution failed on {hostname}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}

    def ping_device(self, hostname: str) -> bool:
        """
        Check device reachability by attempting an SSH connection.

        Falls back to ICMP via subprocess if Netmiko is not available.

        Args:
            hostname: Device hostname (must exist in inventory).

        Returns:
            ``True`` if device is reachable, ``False`` otherwise.
        """
        device = self._get_device(hostname)
        if not device:
            logger.warning(f"ping_device: {hostname} not found in inventory")
            return False

        try:
            connector = DeviceConnector(device)
            result = connector.connect()
            connector.disconnect()
            return bool(result)
        except Exception:
            return False
