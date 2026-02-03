#!/usr/bin/env python3
"""
Kubernetes Network Policy Manager - CLI
Command-line interface for managing network policies.

Author: Navaneethraj KA
"""

import click
import yaml
import json
from rich.console import Console
from rich.table import Table
from netpol.manager import NetworkPolicyManager

console = Console()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Kubernetes Network Policy Manager - Manage, validate, and audit network policies."""
    pass


@cli.command()
@click.option('--namespace', '-n', default='default', help='Kubernetes namespace')
@click.option('--output', '-o', type=click.Choice(['table', 'yaml', 'json']), default='table')
def list(namespace, output):
    """List all network policies in a namespace."""
    npm = NetworkPolicyManager()
    policies = npm.list_policies(namespace)
    
    if output == 'json':
        click.echo(json.dumps(policies, indent=2))
    elif output == 'yaml':
        click.echo(yaml.dump(policies))
    else:
        table = Table(title=f"Network Policies in '{namespace}'")
        table.add_column("Name", style="cyan")
        table.add_column("Pod Selector", style="green")
        table.add_column("Policy Types", style="yellow")
        
        for p in policies:
            table.add_row(
                p['name'],
                str(p.get('pod_selector', 'All')),
                ', '.join(p.get('policy_types', ['Ingress']))
            )
        console.print(table)


@cli.command()
@click.argument('template', type=click.Choice(['deny-all', 'allow-dns', 'allow-web']))
@click.option('--namespace', '-n', default='default')
@click.option('--name', help='Policy name')
@click.option('--output', '-o', default='-', help='Output file (- for stdout)')
def generate(template, namespace, name, output):
    """Generate a network policy from template."""
    npm = NetworkPolicyManager()
    
    if template == 'deny-all':
        policy = npm.generate_deny_all(namespace, name)
    elif template == 'allow-dns':
        policy = npm.generate_allow_dns(namespace, name)
    else:
        policy = npm.generate_allow_web(namespace, name)
    
    policy_yaml = yaml.dump(policy, default_flow_style=False)
    
    if output == '-':
        console.print(policy_yaml)
    else:
        with open(output, 'w') as f:
            f.write(policy_yaml)
        console.print(f"[green]✓ Policy saved to {output}[/green]")


@cli.command()
@click.argument('policy_file', type=click.Path(exists=True))
def validate(policy_file):
    """Validate a network policy file."""
    npm = NetworkPolicyManager()
    
    with open(policy_file) as f:
        policy = yaml.safe_load(f)
    
    issues = npm.validate(policy)
    
    if not issues:
        console.print("[green]✓ Policy is valid![/green]")
    else:
        console.print("[red]Issues found:[/red]")
        for issue in issues:
            severity_color = {'high': 'red', 'medium': 'yellow', 'low': 'blue'}
            console.print(f"  [{severity_color.get(issue['severity'], 'white')}]"
                         f"[{issue['severity'].upper()}][/] {issue['message']}")


@cli.command()
@click.option('--namespace', '-n', default='default')
@click.option('--output', '-o', help='Output report file')
def audit(namespace, output):
    """Audit network policies against security standards."""
    npm = NetworkPolicyManager()
    report = npm.audit(namespace)
    
    console.print(f"\n[bold]Security Audit Report: {namespace}[/bold]\n")
    console.print(f"Score: {report['score']}/100")
    console.print(f"Policies: {report['policy_count']}")
    
    if report['findings']:
        console.print("\n[bold]Findings:[/bold]")
        for finding in report['findings']:
            severity_color = {'high': 'red', 'medium': 'yellow', 'low': 'cyan'}
            console.print(f"  [{severity_color.get(finding['severity'], 'white')}]"
                         f"● {finding['rule']}[/]: {finding['message']}")
    
    if output:
        with open(output, 'w') as f:
            json.dump(report, f, indent=2)
        console.print(f"\n[green]Report saved to {output}[/green]")


@cli.command()
@click.argument('policy_file', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Simulate apply without changes')
def apply(policy_file, dry_run):
    """Apply a network policy to the cluster."""
    npm = NetworkPolicyManager()
    
    with open(policy_file) as f:
        policy = yaml.safe_load(f)
    
    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]")
    
    result = npm.apply(policy, dry_run=dry_run)
    
    if result['success']:
        console.print(f"[green]✓ Policy '{result['name']}' applied successfully[/green]")
    else:
        console.print(f"[red]✗ Failed: {result['error']}[/red]")


@cli.command()
@click.option('--namespace', '-n', default='default')
@click.option('--output', '-o', default='network-policies.png')
def visualize(namespace, output):
    """Generate a visual diagram of network policies."""
    npm = NetworkPolicyManager()
    
    console.print(f"Generating visualization for namespace '{namespace}'...")
    result = npm.visualize(namespace, output)
    
    if result:
        console.print(f"[green]✓ Diagram saved to {output}[/green]")
    else:
        console.print("[yellow]No policies found to visualize[/yellow]")


if __name__ == '__main__':
    cli()
