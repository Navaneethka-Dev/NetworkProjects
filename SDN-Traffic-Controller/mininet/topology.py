#!/usr/bin/env python3
"""
SDN Traffic Controller - Mininet Topology
Custom network topology for testing the SDN controller.

Author: Navaneethraj KA
"""

try:
    from mininet.net import Mininet
    from mininet.node import Controller, RemoteController, OVSSwitch
    from mininet.cli import CLI
    from mininet.log import setLogLevel, info
    from mininet.link import TCLink
    MININET_AVAILABLE = True
except ImportError:
    MININET_AVAILABLE = False
    print("Mininet not available. This script requires Mininet to be installed.")


def create_topology():
    """
    Create a custom network topology for testing.
    
    Topology:
        H1 -- S1 -- S2 -- H2
               |    |
              S3 -- S4
               |    |
              H3   H4 (servers)
    """
    if not MININET_AVAILABLE:
        print("Mininet is not installed. Please install Mininet first.")
        return
    
    setLogLevel('info')
    
    # Create network with remote controller
    net = Mininet(
        controller=RemoteController,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True
    )
    
    info('*** Adding controller\n')
    c0 = net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6653
    )
    
    info('*** Adding switches\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', protocols='OpenFlow13')
    s3 = net.addSwitch('s3', protocols='OpenFlow13')
    s4 = net.addSwitch('s4', protocols='OpenFlow13')
    
    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')  # Server 1
    h4 = net.addHost('h4', ip='10.0.0.4/24')  # Server 2
    
    info('*** Creating links\n')
    # Host links
    net.addLink(h1, s1, bw=100)  # 100 Mbps
    net.addLink(h2, s2, bw=100)
    net.addLink(h3, s3, bw=100)
    net.addLink(h4, s4, bw=100)
    
    # Switch links (backbone)
    net.addLink(s1, s2, bw=1000)  # 1 Gbps backbone
    net.addLink(s1, s3, bw=1000)
    net.addLink(s2, s4, bw=1000)
    net.addLink(s3, s4, bw=1000)
    
    info('*** Starting network\n')
    net.build()
    c0.start()
    
    for switch in [s1, s2, s3, s4]:
        switch.start([c0])
    
    info('*** Network is ready\n')
    info('*** Hosts:\n')
    for host in net.hosts:
        info(f'    {host.name}: {host.IP()}\n')
    
    info('\n*** Running CLI\n')
    CLI(net)
    
    info('*** Stopping network\n')
    net.stop()


def create_load_balancer_topology():
    """
    Create a topology for load balancer testing.
    
    Topology:
        Client -- S1 -- S2 -- Server1
                        |
                       Server2
    """
    if not MININET_AVAILABLE:
        print("Mininet is not installed.")
        return
    
    setLogLevel('info')
    
    net = Mininet(
        controller=RemoteController,
        switch=OVSSwitch,
        link=TCLink
    )
    
    info('*** Adding controller\n')
    c0 = net.addController('c0', ip='127.0.0.1', port=6653)
    
    info('*** Adding switches\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', protocols='OpenFlow13')
    
    info('*** Adding hosts\n')
    client = net.addHost('client', ip='10.0.0.1/24')
    server1 = net.addHost('server1', ip='10.0.0.2/24')
    server2 = net.addHost('server2', ip='10.0.0.3/24')
    
    info('*** Creating links\n')
    net.addLink(client, s1)
    net.addLink(s1, s2)
    net.addLink(server1, s2)
    net.addLink(server2, s2)
    
    info('*** Starting network\n')
    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])
    
    # Start simple HTTP servers on the servers
    info('*** Starting HTTP servers on server hosts\n')
    server1.cmd('python3 -m http.server 80 &')
    server2.cmd('python3 -m http.server 80 &')
    
    info('*** Network ready for load balancer testing\n')
    info('*** Virtual IP: 10.0.0.100 (configure in controller)\n')
    
    CLI(net)
    net.stop()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'lb':
        print("Creating Load Balancer test topology...")
        create_load_balancer_topology()
    else:
        print("Creating default topology...")
        create_topology()
