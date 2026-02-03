#!/usr/bin/env python3
"""
Network Monitoring Dashboard - Entry Point
Start the Flask/Dash application.

Author: Navaneethraj KA
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import create_app, start_polling

def main():
    """Main entry point."""
    print("="*60)
    print("  Network Monitoring Dashboard v1.0")
    print("  Author: Navaneethraj KA")
    print("="*60)
    
    app = create_app()
    
    # Start background polling
    print("\n[INFO] Starting SNMP polling service...")
    start_polling()
    
    print("[INFO] Dashboard available at http://localhost:5000")
    print("[INFO] Press Ctrl+C to stop.\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('DEBUG', 'false').lower() == 'true'
    )

if __name__ == '__main__':
    main()
