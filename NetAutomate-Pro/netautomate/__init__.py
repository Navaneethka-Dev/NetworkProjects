"""
NetAutomate Pro - Network Automation Package
"""

from .core import NetworkAutomation
from .connectors import DeviceConnector
from .backup import BackupManager
from .compliance import ComplianceChecker
from .scheduler import NetAutomateScheduler
from .reporter import ReportGenerator

__version__ = '1.1.0'
__author__ = 'Navaneethraj KA'
__email__ = 'nvnthrj@gmail.com'

__all__ = [
    'NetworkAutomation',
    'DeviceConnector',
    'BackupManager',
    'ComplianceChecker',
    'NetAutomateScheduler',
    'ReportGenerator',
]
