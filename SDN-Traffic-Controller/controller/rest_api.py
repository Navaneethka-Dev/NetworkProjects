#!/usr/bin/env python3
"""
SDN Traffic Controller - REST API
Provides REST API endpoints for network management.

Author: Navaneethraj KA
"""

import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

# Create Flask app
app = Flask(__name__, static_folder='../web')
CORS(app)

# Controller instance (will be set by main controller)
controller = None


def set_controller(ctrl):
    """Set the controller instance."""
    global controller
    controller = ctrl


@app.route('/')
def index():
    """Serve the web dashboard."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/topology', methods=['GET'])
def get_topology():
    """Get network topology."""
    if controller:
        return jsonify(controller.get_topology())
    return jsonify({'error': 'Controller not initialized'}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get traffic statistics."""
    if controller:
        return jsonify(controller.get_stats())
    return jsonify({'error': 'Controller not initialized'}), 500


@app.route('/api/switches', methods=['GET'])
def get_switches():
    """Get all switches."""
    if controller:
        topology = controller.get_topology()
        return jsonify(topology.get('switches', []))
    return jsonify({'error': 'Controller not initialized'}), 500


@app.route('/api/links', methods=['GET'])
def get_links():
    """Get all links."""
    if controller:
        topology = controller.get_topology()
        return jsonify(topology.get('links', []))
    return jsonify({'error': 'Controller not initialized'}), 500


@app.route('/api/hosts', methods=['GET'])
def get_hosts():
    """Get all hosts."""
    if controller:
        topology = controller.get_topology()
        return jsonify(topology.get('hosts', []))
    return jsonify({'error': 'Controller not initialized'}), 500


@app.route('/api/qos', methods=['GET'])
def get_qos_policies():
    """Get QoS policies."""
    if controller:
        return jsonify(controller.qos_policies)
    return jsonify({'error': 'Controller not initialized'}), 500


@app.route('/api/qos', methods=['POST'])
def set_qos_policy():
    """Set a QoS policy."""
    if not controller:
        return jsonify({'error': 'Controller not initialized'}), 500
    
    data = request.get_json()
    required_fields = ['name', 'priority', 'match']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    result = controller.set_qos_policy(
        data['name'],
        data['priority'],
        data['match'],
        data.get('action', 'default')
    )
    
    if result:
        return jsonify({'status': 'success', 'message': f"QoS policy '{data['name']}' created"})
    return jsonify({'error': 'Failed to create QoS policy'}), 500


@app.route('/api/qos/<name>', methods=['DELETE'])
def delete_qos_policy(name):
    """Delete a QoS policy."""
    if not controller:
        return jsonify({'error': 'Controller not initialized'}), 500
    
    if name in controller.qos_policies:
        del controller.qos_policies[name]
        return jsonify({'status': 'success', 'message': f"QoS policy '{name}' deleted"})
    return jsonify({'error': f"Policy '{name}' not found"}), 404


@app.route('/api/loadbalancer', methods=['GET'])
def get_load_balancer():
    """Get load balancer configuration."""
    if controller:
        return jsonify(controller.load_balancer)
    return jsonify({'error': 'Controller not initialized'}), 500


@app.route('/api/loadbalancer', methods=['POST'])
def configure_load_balancer():
    """Configure load balancer."""
    if not controller:
        return jsonify({'error': 'Controller not initialized'}), 500
    
    data = request.get_json()
    
    if 'vip' not in data or 'servers' not in data:
        return jsonify({'error': 'Missing required fields: vip, servers'}), 400
    
    result = controller.configure_load_balancer(
        data['vip'],
        data['servers'],
        data.get('algorithm', 'round_robin')
    )
    
    if result:
        return jsonify({'status': 'success', 'message': 'Load balancer configured'})
    return jsonify({'error': 'Failed to configure load balancer'}), 500


@app.route('/api/loadbalancer/next', methods=['GET'])
def get_next_server():
    """Get next server from load balancer."""
    if controller:
        server = controller.get_next_server()
        if server:
            return jsonify({'server': server})
        return jsonify({'error': 'Load balancer not configured'}), 400
    return jsonify({'error': 'Controller not initialized'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'controller': 'running' if controller else 'not initialized',
        'version': '1.0.0'
    })


def run_api(host='0.0.0.0', port=8080, ctrl=None):
    """Run the REST API server."""
    if ctrl:
        set_controller(ctrl)
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    # For standalone testing
    from main_controller import SDNController
    controller = SDNController()
    controller.demonstrate_features()
    run_api()
