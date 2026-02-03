"""
NetAutomate Pro - Utility Functions
Common utilities for logging, templating, and display.

Author: Navaneethraj KA
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Try to import optional dependencies
try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def setup_logging(log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_file: Optional log file path
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Default log file
    if not log_file:
        log_file = log_dir / f"netautomate_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Create logger
    logger = logging.getLogger('netautomate')
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def render_template(template_file: str, variables: Dict[str, Any]) -> str:
    """
    Render a Jinja2 template with given variables.
    
    Args:
        template_file: Path to template file
        variables: Dictionary of template variables
        
    Returns:
        Rendered template string
    """
    if not JINJA2_AVAILABLE:
        # Simple variable substitution if Jinja2 not available
        template_path = Path(template_file)
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_file}")
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        for key, value in variables.items():
            template_content = template_content.replace(f"{{{{ {key} }}}}", str(value))
        
        return template_content
    
    # Use Jinja2 for proper templating
    template_path = Path(template_file)
    template_dir = template_path.parent
    template_name = template_path.name
    
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    try:
        template = env.get_template(template_name)
        return template.render(**variables)
    except TemplateNotFound:
        raise FileNotFoundError(f"Template not found: {template_file}")


def print_banner():
    """Print the NetAutomate Pro banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███╗   ██╗███████╗████████╗ █████╗ ██╗   ██╗████████╗       ║
║   ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║   ██║╚══██╔══╝       ║
║   ██╔██╗ ██║█████╗     ██║   ███████║██║   ██║   ██║          ║
║   ██║╚██╗██║██╔══╝     ██║   ██╔══██║██║   ██║   ██║          ║
║   ██║ ╚████║███████╗   ██║   ██║  ██║╚██████╔╝   ██║          ║
║   ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝    ╚═╝          ║
║                                                               ║
║                    NetAutomate Pro v1.0                       ║
║           Network Automation Made Simple                      ║
║                                                               ║
║   Author: Navaneethraj KA                                     ║
║   GitHub: github.com/Navaneethka-Dev                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_table(title: str, headers: list, rows: list):
    """
    Print a formatted table.
    
    Args:
        title: Table title
        headers: List of column headers
        rows: List of row data
    """
    if RICH_AVAILABLE:
        console = Console()
        table = Table(title=title)
        
        for header in headers:
            table.add_column(header)
        
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        
        console.print(table)
    else:
        # Simple table format without rich
        print(f"\n{title}")
        print("-" * 60)
        print(" | ".join(f"{h:15}" for h in headers))
        print("-" * 60)
        for row in rows:
            print(" | ".join(f"{str(cell):15}" for cell in row))
        print("-" * 60)


def validate_ip(ip: str) -> bool:
    """
    Validate an IP address.
    
    Args:
        ip: IP address string
        
    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    
    if not re.match(pattern, ip):
        return False
    
    parts = ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts)


def format_bytes(size: int) -> str:
    """
    Format bytes into human-readable format.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def get_timestamp() -> str:
    """Get current timestamp in standard format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
