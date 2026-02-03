#!/usr/bin/env python3
"""
Network Monitoring Dashboard - Alert Manager
Handles alert generation, notification, and management.

Author: Navaneethraj KA
"""

import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class AlertManager:
    """
    Manages alerts and notifications.
    Supports email and webhook notifications.
    """
    
    def __init__(self, config=None):
        """
        Initialize the alert manager.
        
        Args:
            config: Alerting configuration dictionary
        """
        self.config = config or {}
        
        # Email configuration
        self.email_config = self.config.get('email', {})
        self.email_enabled = self.email_config.get('enabled', False)
        
        # Webhook configuration
        self.webhook_config = self.config.get('webhook', {})
        self.webhook_enabled = self.webhook_config.get('enabled', False)
        
        print("[Alert] Alert manager initialized")
    
    def send_alert(self, alert):
        """
        Send an alert notification.
        
        Args:
            alert: Alert dictionary with severity, title, message, device
        """
        if self.email_enabled:
            self._send_email_alert(alert)
        
        if self.webhook_enabled:
            self._send_webhook_alert(alert)
        
        # Always log the alert
        self._log_alert(alert)
    
    def _send_email_alert(self, alert):
        """Send alert via email."""
        try:
            smtp_server = self.email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = self.email_config.get('smtp_port', 587)
            username = self.email_config.get('username')
            password = self.email_config.get('password')
            recipients = self.email_config.get('recipients', [])
            
            if not username or not password or not recipients:
                print("[Alert] Email not configured properly")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[{alert['severity'].upper()}] {alert['title']}"
            
            body = f"""
Network Monitor Alert

Severity: {alert['severity'].upper()}
Device: {alert.get('device', 'Unknown')}
Time: {alert.get('timestamp', datetime.now().isoformat())}

{alert['title']}

{alert.get('message', '')}

---
Network Monitoring Dashboard
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
            print(f"[Alert] Email sent: {alert['title']}")
            
        except Exception as e:
            print(f"[Alert] Email error: {e}")
    
    def _send_webhook_alert(self, alert):
        """Send alert via webhook."""
        try:
            webhook_url = self.webhook_config.get('url')
            
            if not webhook_url:
                return
            
            payload = {
                'severity': alert['severity'],
                'title': alert['title'],
                'message': alert.get('message', ''),
                'device': alert.get('device', 'Unknown'),
                'timestamp': alert.get('timestamp', datetime.now().isoformat()),
                'source': 'Network Monitor Dashboard'
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"[Alert] Webhook sent: {alert['title']}")
            else:
                print(f"[Alert] Webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"[Alert] Webhook error: {e}")
    
    def _log_alert(self, alert):
        """Log alert to console."""
        severity_colors = {
            'critical': '\033[91m',  # Red
            'warning': '\033[93m',   # Yellow
            'info': '\033[94m',      # Blue
        }
        reset = '\033[0m'
        
        color = severity_colors.get(alert['severity'], '')
        print(f"{color}[ALERT] [{alert['severity'].upper()}] {alert['title']}{reset}")
    
    def acknowledge_alert(self, alert_id, user):
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID
            user: User who acknowledged
        """
        from .models import get_session, Alert
        
        session = get_session()
        try:
            alert = session.query(Alert).get(alert_id)
            if alert:
                alert.acknowledged = True
                alert.acknowledged_by = user
                session.commit()
                print(f"[Alert] Alert {alert_id} acknowledged by {user}")
        except Exception as e:
            session.rollback()
            print(f"[Alert] Error acknowledging alert: {e}")
        finally:
            session.close()
    
    def get_active_alerts(self, limit=50):
        """Get active (unacknowledged) alerts."""
        from .models import get_session, Alert
        
        session = get_session()
        try:
            alerts = session.query(Alert).filter(
                Alert.acknowledged == False
            ).order_by(Alert.timestamp.desc()).limit(limit).all()
            
            return [a.to_dict() for a in alerts]
        finally:
            session.close()
