#!/usr/bin/env python3
"""
Network Monitoring Dashboard - Main Application
Flask application with Dash integration for network monitoring.

Author: Navaneethraj KA
"""

import os
import yaml
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd

from .models import init_db, Device, Metric, Alert, get_session
from .snmp_poller import SNMPPoller
from .alerting import AlertManager

# Global instances
poller = None
alert_manager = None


def load_config():
    """Load configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.yaml')
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    # Default configuration
    return {
        'server': {'host': '0.0.0.0', 'port': 5000, 'debug': False},
        'snmp': {'community': 'public', 'version': '2c', 'timeout': 5},
        'polling': {'interval': 60, 'threads': 10},
        'alerting': {'email': {'enabled': False}}
    }


def create_app():
    """Create and configure the Flask application."""
    # Initialize Flask
    server = Flask(__name__)
    server.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'network-monitor-secret-key')
    
    # Initialize database
    init_db()
    
    # Create Dash app
    app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname='/dashboard/',
        external_stylesheets=[dbc.themes.DARKLY]
    )
    
    # Define Dash layout
    app.layout = create_dashboard_layout()
    
    # Register callbacks
    register_callbacks(app)
    
    # Flask routes
    @server.route('/')
    def index():
        """Main page - redirect to dashboard."""
        return render_template('index.html')
    
    @server.route('/api/devices', methods=['GET'])
    def get_devices():
        """Get all devices."""
        session = get_session()
        devices = session.query(Device).all()
        return jsonify([d.to_dict() for d in devices])
    
    @server.route('/api/devices', methods=['POST'])
    def add_device():
        """Add a new device."""
        data = request.get_json()
        session = get_session()
        
        device = Device(
            name=data['name'],
            ip_address=data['ip_address'],
            device_type=data.get('device_type', 'unknown'),
            snmp_community=data.get('snmp_community', 'public')
        )
        
        session.add(device)
        session.commit()
        
        return jsonify({'status': 'success', 'id': device.id})
    
    @server.route('/api/metrics/<device_id>', methods=['GET'])
    def get_metrics(device_id):
        """Get metrics for a device."""
        hours = request.args.get('hours', 24, type=int)
        since = datetime.now() - timedelta(hours=hours)
        
        session = get_session()
        metrics = session.query(Metric).filter(
            Metric.device_id == device_id,
            Metric.timestamp >= since
        ).order_by(Metric.timestamp.desc()).all()
        
        return jsonify([m.to_dict() for m in metrics])
    
    @server.route('/api/alerts', methods=['GET'])
    def get_alerts():
        """Get recent alerts."""
        session = get_session()
        alerts = session.query(Alert).order_by(
            Alert.timestamp.desc()
        ).limit(50).all()
        
        return jsonify([a.to_dict() for a in alerts])
    
    @server.route('/api/stats/summary', methods=['GET'])
    def get_summary_stats():
        """Get summary statistics."""
        session = get_session()
        
        total_devices = session.query(Device).count()
        online_devices = session.query(Device).filter(Device.status == 'online').count()
        active_alerts = session.query(Alert).filter(Alert.acknowledged == False).count()
        
        return jsonify({
            'total_devices': total_devices,
            'online_devices': online_devices,
            'offline_devices': total_devices - online_devices,
            'uptime_percentage': (online_devices / total_devices * 100) if total_devices > 0 else 0,
            'active_alerts': active_alerts
        })
    
    return server


def create_dashboard_layout():
    """Create the Dash dashboard layout."""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("🌐 Network Monitor", className="text-primary mb-4"),
                html.P("Real-time network infrastructure monitoring", className="text-muted")
            ])
        ], className="mt-4"),
        
        # Stats Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(id="total-devices", className="text-center"),
                        html.P("Total Devices", className="text-center text-muted")
                    ])
                ], color="primary", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(id="online-devices", className="text-center text-success"),
                        html.P("Online", className="text-center text-muted")
                    ])
                ], color="success", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(id="offline-devices", className="text-center text-danger"),
                        html.P("Offline", className="text-center text-muted")
                    ])
                ], color="danger", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(id="active-alerts", className="text-center text-warning"),
                        html.P("Active Alerts", className="text-center text-muted")
                    ])
                ], color="warning", outline=True)
            ], width=3)
        ], className="mb-4"),
        
        # Graphs Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Network Traffic (Last 24 Hours)"),
                    dbc.CardBody([
                        dcc.Graph(id="traffic-graph")
                    ])
                ])
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Device Status"),
                    dbc.CardBody([
                        dcc.Graph(id="status-pie")
                    ])
                ])
            ], width=4)
        ], className="mb-4"),
        
        # Device List and Alerts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Device List"),
                    dbc.CardBody([
                        html.Div(id="device-list")
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Recent Alerts"),
                    dbc.CardBody([
                        html.Div(id="alert-list")
                    ])
                ])
            ], width=6)
        ]),
        
        # Auto-refresh interval
        dcc.Interval(
            id='interval-component',
            interval=30*1000,  # 30 seconds
            n_intervals=0
        )
    ], fluid=True)


def register_callbacks(app):
    """Register Dash callbacks for interactivity."""
    
    @app.callback(
        [Output('total-devices', 'children'),
         Output('online-devices', 'children'),
         Output('offline-devices', 'children'),
         Output('active-alerts', 'children')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_stats(n):
        """Update statistics cards."""
        # Simulated data for demonstration
        return "24", "22", "2", "3"
    
    @app.callback(
        Output('traffic-graph', 'figure'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_traffic_graph(n):
        """Update traffic graph."""
        # Generate sample data
        hours = pd.date_range(end=datetime.now(), periods=24, freq='H')
        inbound = [100 + i*5 + (i % 3) * 20 for i in range(24)]
        outbound = [80 + i*4 + (i % 4) * 15 for i in range(24)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hours, y=inbound, name='Inbound',
            line=dict(color='#00d4ff', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=hours, y=outbound, name='Outbound',
            line=dict(color='#7c3aed', width=2)
        ))
        
        fig.update_layout(
            template='plotly_dark',
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            xaxis_title='Time',
            yaxis_title='Mbps'
        )
        
        return fig
    
    @app.callback(
        Output('status-pie', 'figure'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_status_pie(n):
        """Update device status pie chart."""
        fig = go.Figure(data=[go.Pie(
            labels=['Online', 'Offline', 'Warning'],
            values=[22, 2, 3],
            hole=0.4,
            marker_colors=['#10b981', '#ef4444', '#f59e0b']
        )])
        
        fig.update_layout(
            template='plotly_dark',
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=True
        )
        
        return fig
    
    @app.callback(
        Output('device-list', 'children'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_device_list(n):
        """Update device list."""
        # Sample devices
        devices = [
            {'name': 'Core-Router-1', 'ip': '192.168.1.1', 'status': 'online'},
            {'name': 'Core-Switch-1', 'ip': '192.168.1.2', 'status': 'online'},
            {'name': 'Firewall-1', 'ip': '192.168.1.3', 'status': 'online'},
            {'name': 'AP-Floor-2', 'ip': '192.168.1.100', 'status': 'offline'},
            {'name': 'Edge-Router-1', 'ip': '192.168.1.4', 'status': 'warning'},
        ]
        
        rows = []
        for d in devices:
            status_color = {'online': 'success', 'offline': 'danger', 'warning': 'warning'}
            rows.append(
                dbc.Row([
                    dbc.Col(html.Span(
                        "●", 
                        className=f"text-{status_color.get(d['status'], 'secondary')}"
                    ), width=1),
                    dbc.Col(d['name'], width=5),
                    dbc.Col(d['ip'], width=4),
                    dbc.Col(d['status'].upper(), width=2)
                ], className="mb-2")
            )
        
        return rows
    
    @app.callback(
        Output('alert-list', 'children'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_alert_list(n):
        """Update alert list."""
        alerts = [
            {'time': '2 min ago', 'device': 'AP-Floor-2', 'message': 'Device unreachable', 'severity': 'critical'},
            {'time': '15 min ago', 'device': 'Edge-Router-1', 'message': 'High CPU usage (92%)', 'severity': 'warning'},
            {'time': '1 hour ago', 'device': 'Core-Switch-1', 'message': 'Port Gi0/24 down', 'severity': 'warning'},
        ]
        
        rows = []
        for a in alerts:
            severity_color = {'critical': 'danger', 'warning': 'warning', 'info': 'info'}
            rows.append(
                dbc.Alert([
                    html.Strong(f"[{a['severity'].upper()}] "),
                    f"{a['device']}: {a['message']}",
                    html.Small(f" ({a['time']})", className="text-muted")
                ], color=severity_color.get(a['severity'], 'secondary'), className="mb-2 py-2")
            )
        
        return rows


def start_polling():
    """Start the SNMP polling service in a background thread."""
    global poller, alert_manager
    
    config = load_config()
    
    poller = SNMPPoller(
        community=config['snmp']['community'],
        timeout=config['snmp']['timeout'],
        interval=config['polling']['interval']
    )
    
    alert_manager = AlertManager(config.get('alerting', {}))
    
    # Start polling thread
    polling_thread = threading.Thread(target=poller.run, daemon=True)
    polling_thread.start()
    
    print("[INFO] SNMP polling service started")
