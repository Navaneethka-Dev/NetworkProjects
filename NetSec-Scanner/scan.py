#!/usr/bin/env python3
"""
Network Security Scanner - CLI Entry Point
Command-line interface for the security scanner.

Author: Navaneethraj KA
"""

import argparse
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner.core import SecurityScanner
from scanner.report import ReportGenerator

# Colors for terminal output
try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = RESET = ''
    class Style:
        BRIGHT = RESET_ALL = ''


def print_banner():
    """Print the scanner banner."""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════╗
║              {Fore.WHITE}NETWORK SECURITY SCANNER v1.0{Fore.CYAN}                    ║
║              {Fore.YELLOW}Author: Navaneethraj KA{Fore.CYAN}                          ║
╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Network Security Scanner - Vulnerability Assessment Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan.py -t 192.168.1.100           # Basic scan
  python scan.py -t 192.168.1.0/24 --quick  # Quick network scan
  python scan.py -t 192.168.1.100 --full    # Full vulnerability scan
  python scan.py -t example.com --web       # Web application scan
        """
    )
    
    parser.add_argument('-t', '--target', required=True,
                        help='Target IP, hostname, or CIDR range')
    parser.add_argument('-p', '--ports', default='1-1000',
                        help='Port range to scan (default: 1-1000)')
    parser.add_argument('--quick', action='store_true',
                        help='Quick scan (top 100 ports only)')
    parser.add_argument('--full', action='store_true',
                        help='Full scan with vulnerability detection')
    parser.add_argument('--udp', action='store_true',
                        help='Include UDP port scan')
    parser.add_argument('--ssl', action='store_true',
                        help='SSL/TLS analysis')
    parser.add_argument('--web', action='store_true',
                        help='Web application vulnerability scan')
    parser.add_argument('--threads', type=int, default=100,
                        help='Number of threads (default: 100)')
    parser.add_argument('--timeout', type=float, default=2.0,
                        help='Connection timeout in seconds (default: 2.0)')
    parser.add_argument('--report', choices=['html', 'json', 'pdf', 'txt'],
                        default='html', help='Report format (default: html)')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    
    return parser.parse_args()


def main():
    """Main entry point."""
    print_banner()
    args = parse_arguments()
    
    print(f"{Fore.WHITE}[*] Target: {Fore.CYAN}{args.target}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Scan Type: {Fore.CYAN}{'Full' if args.full else 'Quick' if args.quick else 'Normal'}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Starting scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    print()
    
    try:
        # Create scanner
        scanner = SecurityScanner(
            threads=args.threads,
            timeout=args.timeout,
            verbose=args.verbose
        )
        
        # Determine scan type
        scan_type = 'full' if args.full else 'quick' if args.quick else 'normal'
        
        # Run scan
        results = scanner.scan(
            target=args.target,
            ports=args.ports,
            scan_type=scan_type,
            include_udp=args.udp,
            ssl_check=args.ssl,
            web_check=args.web
        )
        
        # Print results summary
        print_results(results)
        
        # Generate report
        if args.output:
            output_path = args.output
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"reports/scan_{timestamp}.{args.report}"
        
        report_gen = ReportGenerator()
        report_gen.generate(results, output_path, format=args.report)
        
        print(f"\n{Fore.GREEN}[+] Report saved: {output_path}{Style.RESET_ALL}")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Scan interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def print_results(results):
    """Print scan results to terminal."""
    # Print host discovery results
    if results.get('hosts'):
        print(f"\n{Fore.GREEN}[+] Host Discovery{Style.RESET_ALL}")
        for host in results['hosts']:
            status = f"{Fore.GREEN}UP{Style.RESET_ALL}" if host['status'] == 'up' else f"{Fore.RED}DOWN{Style.RESET_ALL}"
            os_info = f" ({host.get('os', 'Unknown')})" if host.get('os') else ""
            print(f"    ├── {host['ip']:15} - {status}{os_info}")
    
    # Print port scan results
    if results.get('ports'):
        print(f"\n{Fore.GREEN}[+] Open Ports{Style.RESET_ALL}")
        for host_ip, ports in results['ports'].items():
            print(f"    {Fore.CYAN}{host_ip}{Style.RESET_ALL}")
            for port in ports:
                state = f"{Fore.GREEN}OPEN{Style.RESET_ALL}" if port['state'] == 'open' else f"{Fore.YELLOW}{port['state'].upper()}{Style.RESET_ALL}"
                service = port.get('service', 'unknown')
                version = port.get('version', '')
                print(f"    ├── {port['port']}/{port['protocol']:4} {state:12} {service:12} {version}")
    
    # Print vulnerabilities
    if results.get('vulnerabilities'):
        print(f"\n{Fore.RED}[!] Vulnerabilities Found{Style.RESET_ALL}")
        for vuln in results['vulnerabilities']:
            severity_colors = {
                'critical': Fore.RED,
                'high': Fore.RED,
                'medium': Fore.YELLOW,
                'low': Fore.CYAN,
                'info': Fore.WHITE
            }
            color = severity_colors.get(vuln['severity'].lower(), Fore.WHITE)
            print(f"    ├── {color}{vuln['severity'].upper():8}{Style.RESET_ALL} {vuln['title']} ({vuln['host']})")
    
    # Print summary
    print(f"\n{Fore.GREEN}[+] Scan completed in {results.get('duration', 0):.1f} seconds{Style.RESET_ALL}")
    print(f"    Hosts: {len(results.get('hosts', []))} | Ports: {sum(len(p) for p in results.get('ports', {}).values())} | Vulnerabilities: {len(results.get('vulnerabilities', []))}")


if __name__ == '__main__':
    main()
