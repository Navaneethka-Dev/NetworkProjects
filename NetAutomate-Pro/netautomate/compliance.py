"""
NetAutomate Pro - Compliance Checker
Checks device configurations against security and operational standards.

Author: Navaneethraj KA
"""

import os
import re
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path

from .utils import setup_logging

logger = setup_logging()


class ComplianceChecker:
    """
    Checks device configurations against defined standards.
    Supports custom compliance rules and generates detailed reports.
    """
    
    # Default compliance rules
    DEFAULT_RULES = {
        'security': [
            {
                'name': 'SSH Enabled',
                'description': 'SSH should be enabled for secure management',
                'pattern': r'transport input ssh',
                'required': True,
                'severity': 'high'
            },
            {
                'name': 'Telnet Disabled',
                'description': 'Telnet should be disabled',
                'pattern': r'transport input telnet',
                'required': False,
                'severity': 'high'
            },
            {
                'name': 'Enable Secret Set',
                'description': 'Enable secret should be configured',
                'pattern': r'enable secret',
                'required': True,
                'severity': 'critical'
            },
            {
                'name': 'Password Encryption',
                'description': 'Password encryption service should be enabled',
                'pattern': r'service password-encryption',
                'required': True,
                'severity': 'high'
            },
            {
                'name': 'Login Banner',
                'description': 'Login banner should be configured',
                'pattern': r'banner (login|motd)',
                'required': True,
                'severity': 'medium'
            },
            {
                'name': 'Logging Enabled',
                'description': 'Logging should be configured',
                'pattern': r'logging (host|buffered)',
                'required': True,
                'severity': 'medium'
            },
            {
                'name': 'NTP Configured',
                'description': 'NTP should be configured for time synchronization',
                'pattern': r'ntp server',
                'required': True,
                'severity': 'medium'
            },
            {
                'name': 'No HTTP Server',
                'description': 'HTTP server should be disabled',
                'pattern': r'no ip http server',
                'required': True,
                'severity': 'high'
            }
        ],
        'operational': [
            {
                'name': 'Hostname Configured',
                'description': 'Hostname should be set',
                'pattern': r'^hostname \S+',
                'required': True,
                'severity': 'low'
            },
            {
                'name': 'Domain Name Set',
                'description': 'Domain name should be configured',
                'pattern': r'ip domain.name',
                'required': True,
                'severity': 'low'
            },
            {
                'name': 'SNMP Configured',
                'description': 'SNMP should be configured for monitoring',
                'pattern': r'snmp-server community',
                'required': True,
                'severity': 'medium'
            }
        ]
    }
    
    def __init__(self, rules_file: str = None):
        """
        Initialize the compliance checker.
        
        Args:
            rules_file: Optional path to custom rules file
        """
        if rules_file and os.path.exists(rules_file):
            with open(rules_file, 'r') as f:
                self.rules = yaml.safe_load(f)
        else:
            self.rules = self.DEFAULT_RULES
        
        logger.info("ComplianceChecker initialized")
    
    def check(self, config: str, standards_file: str = None) -> Dict[str, Any]:
        """
        Check configuration against compliance standards.
        
        Args:
            config: Device configuration string
            standards_file: Optional path to standards file
            
        Returns:
            Compliance report dictionary
        """
        if standards_file and os.path.exists(standards_file):
            with open(standards_file, 'r') as f:
                rules = yaml.safe_load(f)
        else:
            rules = self.rules
        
        violations = []
        passed = []
        recommendations = []
        
        total_rules = 0
        passed_count = 0
        
        # Check each category
        for category, category_rules in rules.items():
            for rule in category_rules:
                total_rules += 1
                result = self._check_rule(config, rule)
                
                if result['passed']:
                    passed_count += 1
                    passed.append({
                        'name': rule['name'],
                        'category': category,
                        'severity': rule.get('severity', 'medium')
                    })
                else:
                    violations.append({
                        'name': rule['name'],
                        'description': rule['description'],
                        'category': category,
                        'severity': rule.get('severity', 'medium')
                    })
                    
                    if rule.get('recommendation'):
                        recommendations.append(rule['recommendation'])
        
        # Calculate compliance score
        score = int((passed_count / total_rules) * 100) if total_rules > 0 else 0
        
        # Determine overall compliance status
        critical_violations = [v for v in violations if v['severity'] == 'critical']
        compliant = score >= 80 and len(critical_violations) == 0
        
        # Generate recommendations based on violations
        if not recommendations:
            recommendations = self._generate_recommendations(violations)
        
        return {
            'compliant': compliant,
            'score': score,
            'total_rules': total_rules,
            'passed': len(passed),
            'violations': [f"{v['severity'].upper()}: {v['name']} - {v['description']}" for v in violations],
            'violation_details': violations,
            'passed_details': passed,
            'recommendations': recommendations,
            'summary': self._generate_summary(score, violations)
        }
    
    def _check_rule(self, config: str, rule: Dict) -> Dict[str, Any]:
        """
        Check a single rule against the configuration.
        
        Args:
            config: Device configuration
            rule: Rule dictionary
            
        Returns:
            Result dictionary with passed status and details
        """
        pattern = rule['pattern']
        required = rule.get('required', True)
        
        # Search for the pattern
        match = re.search(pattern, config, re.MULTILINE | re.IGNORECASE)
        
        if required:
            # Pattern should be present
            passed = match is not None
        else:
            # Pattern should be absent
            passed = match is None
        
        return {
            'passed': passed,
            'rule': rule['name'],
            'found': match is not None
        }
    
    def _generate_recommendations(self, violations: List[Dict]) -> List[str]:
        """Generate remediation recommendations based on violations."""
        recommendations = []
        
        recommendation_map = {
            'SSH Enabled': 'Configure SSH: "line vty 0 4" then "transport input ssh"',
            'Telnet Disabled': 'Disable Telnet: "line vty 0 4" then "transport input ssh"',
            'Enable Secret Set': 'Set enable secret: "enable secret <password>"',
            'Password Encryption': 'Enable encryption: "service password-encryption"',
            'Login Banner': 'Configure banner: "banner motd #Authorized access only#"',
            'Logging Enabled': 'Configure logging: "logging buffered 4096" and "logging host <syslog-server>"',
            'NTP Configured': 'Configure NTP: "ntp server <ntp-server-ip>"',
            'No HTTP Server': 'Disable HTTP: "no ip http server" and "no ip http secure-server"',
            'SNMP Configured': 'Configure SNMP: "snmp-server community <community> RO"'
        }
        
        for violation in violations:
            if violation['name'] in recommendation_map:
                recommendations.append(recommendation_map[violation['name']])
        
        return recommendations
    
    def _generate_summary(self, score: int, violations: List[Dict]) -> str:
        """Generate a human-readable summary."""
        if score >= 90:
            status = "Excellent"
        elif score >= 80:
            status = "Good"
        elif score >= 60:
            status = "Needs Improvement"
        else:
            status = "Critical"
        
        critical_count = len([v for v in violations if v['severity'] == 'critical'])
        high_count = len([v for v in violations if v['severity'] == 'high'])
        
        summary = f"Compliance Status: {status} ({score}%)"
        
        if critical_count > 0:
            summary += f" | {critical_count} Critical Issue(s)"
        if high_count > 0:
            summary += f" | {high_count} High Issue(s)"
        
        return summary
    
    def add_custom_rule(self, category: str, rule: Dict):
        """
        Add a custom compliance rule.
        
        Args:
            category: Rule category (security, operational, etc.)
            rule: Rule dictionary with name, description, pattern, required, severity
        """
        if category not in self.rules:
            self.rules[category] = []
        
        self.rules[category].append(rule)
        logger.info(f"Added custom rule: {rule['name']} to category: {category}")
    
    def export_rules(self, filepath: str):
        """Export current rules to a YAML file."""
        with open(filepath, 'w') as f:
            yaml.dump(self.rules, f, default_flow_style=False)
        logger.info(f"Rules exported to: {filepath}")
