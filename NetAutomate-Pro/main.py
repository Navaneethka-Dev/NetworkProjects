#!/usr/bin/env python3
"""
NetAutomate Pro - Network Automation Tool
A comprehensive Python-based network automation solution for multi-vendor environments.

Author: Navaneethraj KA
Email: nvnthrj@gmail.com
GitHub: https://github.com/Navaneethka-Dev
"""

import click
import yaml
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from netautomate.core import NetworkAutomation
from netautomate.utils import setup_logging, print_banner

# Setup logging
logger = setup_logging()

@click.group()
@click.version_option(version='1.0.0', prog_name='NetAutomate Pro')
def cli():
    """
    🌐 NetAutomate Pro - Network Automation Tool
    
    Automate network device configurations across multi-vendor environments.
    Supports Cisco IOS, NX-OS, and Juniper Junos devices.
    """
    print_banner()

@cli.command()
@click.option('--device', '-d', help='Specific device hostname to backup')
@click.option('--all', '-a', 'all_devices', is_flag=True, help='Backup all devices')
@click.option('--inventory', '-i', default='inventory/devices.yaml', help='Inventory file path')
def backup(device, all_devices, inventory):
    """
    📦 Backup device configurations
    
    Saves running configurations to the backups/ directory with timestamps.
    """
    try:
        na = NetworkAutomation(inventory)
        
        if all_devices:
            click.echo(click.style("\n📦 Backing up ALL devices...\n", fg='cyan', bold=True))
            results = na.backup_all_devices()
            
            success = sum(1 for r in results if r['status'] == 'success')
            failed = sum(1 for r in results if r['status'] == 'failed')
            
            click.echo(click.style(f"\n✅ Backup Complete: {success} succeeded, {failed} failed", 
                                   fg='green' if failed == 0 else 'yellow', bold=True))
        elif device:
            click.echo(click.style(f"\n📦 Backing up {device}...\n", fg='cyan', bold=True))
            result = na.backup_device(device)
            
            if result['status'] == 'success':
                click.echo(click.style(f"✅ Backup saved: {result['backup_file']}", fg='green'))
            else:
                click.echo(click.style(f"❌ Backup failed: {result['error']}", fg='red'))
        else:
            click.echo(click.style("⚠️  Please specify --device or --all", fg='yellow'))
            
    except FileNotFoundError:
        click.echo(click.style(f"❌ Inventory file not found: {inventory}", fg='red'))
    except Exception as e:
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))
        logger.exception("Backup command failed")

@cli.command()
@click.option('--device', '-d', help='Specific device hostname')
@click.option('--all', '-a', 'all_devices', is_flag=True, help='Deploy to all devices')
@click.option('--template', '-t', required=True, help='Template file to deploy')
@click.option('--vars', '-v', help='Variables file (YAML)')
@click.option('--dry-run', is_flag=True, help='Preview changes without applying')
@click.option('--inventory', '-i', default='inventory/devices.yaml', help='Inventory file path')
def deploy(device, all_devices, template, vars, dry_run, inventory):
    """
    🚀 Deploy configurations to devices
    
    Uses Jinja2 templates for dynamic configuration generation.
    Use --dry-run to preview changes before applying.
    """
    try:
        na = NetworkAutomation(inventory)
        
        # Load variables if provided
        variables = {}
        if vars:
            with open(vars, 'r') as f:
                variables = yaml.safe_load(f)
        
        mode = "DRY-RUN" if dry_run else "LIVE"
        click.echo(click.style(f"\n🚀 Deployment Mode: {mode}\n", fg='cyan', bold=True))
        
        if all_devices:
            results = na.deploy_to_all(template, variables, dry_run=dry_run)
            
            success = sum(1 for r in results if r['status'] == 'success')
            failed = sum(1 for r in results if r['status'] == 'failed')
            
            click.echo(click.style(f"\n✅ Deployment Complete: {success} succeeded, {failed} failed", 
                                   fg='green' if failed == 0 else 'yellow', bold=True))
        elif device:
            result = na.deploy_config(device, template, variables, dry_run=dry_run)
            
            if result['status'] == 'success':
                click.echo(click.style(f"✅ Configuration deployed to {device}", fg='green'))
                if dry_run:
                    click.echo(click.style("\n📋 Generated Configuration:", fg='cyan'))
                    click.echo(result.get('config_preview', ''))
            else:
                click.echo(click.style(f"❌ Deployment failed: {result['error']}", fg='red'))
        else:
            click.echo(click.style("⚠️  Please specify --device or --all", fg='yellow'))
            
    except Exception as e:
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))
        logger.exception("Deploy command failed")

@cli.command()
@click.option('--device', '-d', help='Specific device hostname')
@click.option('--all', '-a', 'all_devices', is_flag=True, help='Check all devices')
@click.option('--standards', '-s', default='configs/standards.yaml', help='Standards file')
@click.option('--inventory', '-i', default='inventory/devices.yaml', help='Inventory file path')
def compliance(device, all_devices, standards, inventory):
    """
    🔍 Check device compliance against standards
    
    Verifies configurations match defined security and operational standards.
    """
    try:
        na = NetworkAutomation(inventory)
        
        click.echo(click.style("\n🔍 Running Compliance Check...\n", fg='cyan', bold=True))
        
        if all_devices:
            results = na.check_compliance_all(standards)
            
            for result in results:
                status_icon = "✅" if result['compliant'] else "❌"
                status_color = 'green' if result['compliant'] else 'red'
                click.echo(click.style(f"{status_icon} {result['device']}: {result['score']}% compliant", 
                                       fg=status_color))
                
                if not result['compliant'] and result.get('violations'):
                    for v in result['violations']:
                        click.echo(click.style(f"   ⚠️  {v}", fg='yellow'))
        elif device:
            result = na.check_compliance(device, standards)
            
            status_icon = "✅" if result['compliant'] else "❌"
            status_color = 'green' if result['compliant'] else 'red'
            click.echo(click.style(f"{status_icon} {device}: {result['score']}% compliant", 
                                   fg=status_color, bold=True))
            
            if result.get('violations'):
                click.echo(click.style("\n⚠️  Violations Found:", fg='yellow'))
                for v in result['violations']:
                    click.echo(f"   - {v}")
            
            if result.get('recommendations'):
                click.echo(click.style("\n💡 Recommendations:", fg='cyan'))
                for r in result['recommendations']:
                    click.echo(f"   - {r}")
        else:
            click.echo(click.style("⚠️  Please specify --device or --all", fg='yellow'))
            
    except Exception as e:
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))
        logger.exception("Compliance command failed")

@cli.command()
@click.option('--inventory', '-i', default='inventory/devices.yaml', help='Inventory file path')
def inventory_list(inventory):
    """
    📋 List all devices in inventory
    """
    try:
        na = NetworkAutomation(inventory)
        devices = na.list_devices()
        
        click.echo(click.style("\n📋 Device Inventory\n", fg='cyan', bold=True))
        click.echo("-" * 60)
        
        for device in devices:
            status = "🟢" if device.get('reachable', True) else "🔴"
            click.echo(f"{status} {device['hostname']:20} {device['ip']:15} {device['device_type']}")
        
        click.echo("-" * 60)
        click.echo(f"Total: {len(devices)} devices")
        
    except Exception as e:
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))

@cli.command()
@click.argument('device')
@click.argument('command')
@click.option('--inventory', '-i', default='inventory/devices.yaml', help='Inventory file path')
def execute(device, command, inventory):
    """
    ⚡ Execute a command on a device
    
    Example: netautomate execute router1 "show ip interface brief"
    """
    try:
        na = NetworkAutomation(inventory)
        
        click.echo(click.style(f"\n⚡ Executing on {device}: {command}\n", fg='cyan', bold=True))
        
        result = na.execute_command(device, command)
        
        if result['status'] == 'success':
            click.echo(click.style("📤 Output:", fg='green'))
            click.echo(result['output'])
        else:
            click.echo(click.style(f"❌ Error: {result['error']}", fg='red'))
            
    except Exception as e:
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))

if __name__ == '__main__':
    cli()
