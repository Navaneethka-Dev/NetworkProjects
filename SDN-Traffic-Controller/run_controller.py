#!/usr/bin/env python3
"""
SDN Traffic Controller - Entry Point
Start the Ryu SDN controller with all modules.

Author: Navaneethraj KA
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the SDN controller."""
    try:
        from ryu.cmd import manager
    except ImportError:
        print("="*60)
        print("Ryu SDN Framework not installed!")
        print("Install with: pip install ryu")
        print("="*60)
        print("\nRunning in simulation mode for demonstration...\n")
        run_simulation()
        return
    
    # Ryu manager arguments
    args = [
        '',  # Placeholder for script name
        'controller.main_controller',
        '--observe-links',
        '--verbose',
        '--ofp-listen-host', '0.0.0.0',
        '--ofp-tcp-listen-port', '6653',
        '--wsapi-host', '0.0.0.0',
        '--wsapi-port', '8080',
    ]
    
    sys.argv = args
    manager.main()


def run_simulation():
    """Run a simulation without actual Ryu."""
    from controller.main_controller import SDNController
    
    print("="*60)
    print("  SDN Traffic Controller - Simulation Mode")
    print("="*60)
    
    controller = SDNController()
    
    # Simulate some operations
    print("\n[INFO] Initializing controller components...")
    print("[INFO] Topology Manager: Ready")
    print("[INFO] Traffic Monitor: Ready")
    print("[INFO] QoS Manager: Ready")
    print("[INFO] Load Balancer: Ready")
    print("[INFO] REST API: Ready on http://localhost:8080")
    
    print("\n[INFO] Waiting for switch connections...")
    print("[INFO] Use Mininet to connect switches to this controller")
    print("\n[SIMULATION] Demonstrating controller capabilities:\n")
    
    # Demonstrate features
    controller.demonstrate_features()
    
    print("\n[INFO] Controller is ready!")
    print("[INFO] Press Ctrl+C to stop.\n")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down controller...")


if __name__ == '__main__':
    main()
