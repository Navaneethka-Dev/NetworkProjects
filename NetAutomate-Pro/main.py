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
import io
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output on Windows (cp1252 can't encode emoji)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add the package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from netautomate.core import NetworkAutomation
from netautomate.utils import setup_logging, print_banner
from netautomate.reporter import ReportGenerator
from netautomate.backup import BackupManager

# Setup logging
logger = setup_logging()

@click.group()
@click.version_option(version='1.1.0', prog_name='NetAutomate Pro')
def cli():
    """
    NetAutomate Pro - Network Automation Tool

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

@cli.command()
@click.option('--type', '-t', 'report_type',
              type=click.Choice(['compliance', 'backup'], case_sensitive=False),
              default='compliance', show_default=True,
              help='Type of report to generate.')
@click.option('--format', '-f', 'fmt',
              type=click.Choice(['html', 'json'], case_sensitive=False),
              default='html', show_default=True,
              help='Output format.')
@click.option('--output-dir', '-o', default='reports', show_default=True,
              help='Directory to write the report into.')
@click.option('--inventory', '-i', default='inventory/devices.yaml',
              help='Inventory file path.')
@click.option('--standards', '-s', default='configs/standards.yaml',
              help='Compliance standards file (compliance reports only).')
def report(report_type, fmt, output_dir, inventory, standards):
    """
    📊 Generate HTML or JSON reports

    \b
    Examples:
      python main.py report --type compliance --format html
      python main.py report --type backup     --format json
    """
    try:
        reporter = ReportGenerator(output_dir=output_dir)

        if report_type == 'compliance':
            na = NetworkAutomation(inventory)
            click.echo(click.style(
                f"\n🔍 Running compliance checks on {len(na.devices)} device(s)…\n",
                fg='cyan', bold=True
            ))
            results = na.check_compliance_all(standards_file=standards)
            path = reporter.generate_compliance_report(results, fmt=fmt)

        else:  # backup
            bm = BackupManager()
            backups = bm.list_backups()
            path = reporter.generate_backup_report(backups, fmt=fmt)

        click.echo(click.style(f"✅ Report generated: {path}", fg='green', bold=True))

    except FileNotFoundError as exc:
        click.echo(click.style(f"❌ File not found: {exc}", fg='red'))
    except Exception as exc:
        click.echo(click.style(f"❌ Error: {exc}", fg='red'))
        logger.exception("Report command failed")


@cli.command('schedule')
@click.option('--backup-hours', default=6, show_default=True,
              help='Run fleet backup every N hours (0 = disabled).')
@click.option('--health-minutes', default=15, show_default=True,
              help='Run device health-checks every N minutes (0 = disabled).')
@click.option('--inventory', '-i', default='inventory/devices.yaml',
              help='Inventory file path.')
def schedule_cmd(backup_hours, health_minutes, inventory):
    """
    ⏰ Start the background scheduler

    Runs periodic backups and health-checks in the foreground.
    Press Ctrl-C to stop.

    \b
    Example:
      python main.py schedule --backup-hours 6 --health-minutes 15
    """
    try:
        from netautomate.scheduler import NetAutomateScheduler

        na = NetworkAutomation(inventory)
        sched = NetAutomateScheduler(na)

        if backup_hours > 0:
            sched.schedule_backups(interval_hours=backup_hours)
            click.echo(click.style(
                f"  📦 Backups scheduled every {backup_hours}h", fg='cyan'))

        if health_minutes > 0:
            sched.schedule_health_checks(interval_minutes=health_minutes)
            click.echo(click.style(
                f"  💓 Health checks scheduled every {health_minutes}m", fg='cyan'))

        click.echo(click.style("\n⏰ Scheduler running. Press Ctrl-C to stop.\n",
                               fg='green', bold=True))
        sched.start(blocking=True)

    except ImportError:
        click.echo(click.style(
            "❌ 'schedule' library not installed. Run: pip install schedule",
            fg='red'))
    except Exception as exc:
        click.echo(click.style(f"❌ Error: {exc}", fg='red'))
        logger.exception("Schedule command failed")


if __name__ == '__main__':
    cli()
