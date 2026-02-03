#!/usr/bin/env python3
"""
SDN Traffic Controller - Main Controller
Ryu-based SDN controller with traffic management, QoS, and load balancing.

Author: Navaneethraj KA
Email: nvnthrj@gmail.com
"""

import json
import logging
from datetime import datetime
from collections import defaultdict

# Try to import Ryu components
try:
    from ryu.base import app_manager
    from ryu.controller import ofp_event
    from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
    from ryu.ofproto import ofproto_v1_3
    from ryu.lib.packet import packet, ethernet, ipv4, arp, icmp, tcp, udp
    from ryu.lib import hub
    from ryu.topology import event as topo_event
    from ryu.topology.api import get_switch, get_link
    RYU_AVAILABLE = True
except ImportError:
    RYU_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SDNController')


class SDNController:
    """
    Main SDN Controller class.
    Handles OpenFlow switch connections, packet processing, and network management.
    """
    
    # OpenFlow protocol version
    OFP_VERSIONS = [4]  # OpenFlow 1.3
    
    def __init__(self):
        """Initialize the SDN controller."""
        self.name = 'SDNController'
        
        # Network state
        self.switches = {}
        self.mac_to_port = defaultdict(dict)
        self.topology = {'switches': [], 'links': [], 'hosts': []}
        
        # Traffic statistics
        self.flow_stats = defaultdict(dict)
        self.port_stats = defaultdict(dict)
        
        # QoS configuration
        self.qos_policies = {}
        self.priority_queues = {
            'high': 1,
            'medium': 2,
            'low': 3
        }
        
        # Load balancer state
        self.load_balancer = {
            'enabled': False,
            'virtual_ip': None,
            'servers': [],
            'algorithm': 'round_robin',
            'current_index': 0
        }
        
        logger.info("SDN Controller initialized")
    
    def demonstrate_features(self):
        """Demonstrate controller features in simulation mode."""
        print("1. Topology Discovery")
        print("   - Discovering network switches and links...")
        self._simulate_topology_discovery()
        
        print("\n2. Traffic Monitoring")
        print("   - Collecting flow statistics...")
        self._simulate_traffic_stats()
        
        print("\n3. QoS Policy Management")
        print("   - Applying QoS policies...")
        self._simulate_qos()
        
        print("\n4. Load Balancing")
        print("   - Configuring load balancer...")
        self._simulate_load_balancer()
    
    def _simulate_topology_discovery(self):
        """Simulate topology discovery."""
        self.topology = {
            'switches': [
                {'dpid': 1, 'name': 'S1', 'ports': 4},
                {'dpid': 2, 'name': 'S2', 'ports': 4},
                {'dpid': 3, 'name': 'S3', 'ports': 4}
            ],
            'links': [
                {'src': 'S1:2', 'dst': 'S2:1', 'bandwidth': '1Gbps'},
                {'src': 'S2:2', 'dst': 'S3:1', 'bandwidth': '1Gbps'},
                {'src': 'S1:3', 'dst': 'S3:2', 'bandwidth': '1Gbps'}
            ],
            'hosts': [
                {'mac': '00:00:00:00:00:01', 'ip': '10.0.0.1', 'switch': 'S1'},
                {'mac': '00:00:00:00:00:02', 'ip': '10.0.0.2', 'switch': 'S2'},
                {'mac': '00:00:00:00:00:03', 'ip': '10.0.0.3', 'switch': 'S3'}
            ]
        }
        
        print(f"   ✓ Discovered {len(self.topology['switches'])} switches")
        print(f"   ✓ Discovered {len(self.topology['links'])} links")
        print(f"   ✓ Discovered {len(self.topology['hosts'])} hosts")
    
    def _simulate_traffic_stats(self):
        """Simulate traffic statistics."""
        self.flow_stats = {
            'S1': {
                'flow_1': {'packets': 15234, 'bytes': 18280800, 'duration': 120},
                'flow_2': {'packets': 8921, 'bytes': 10705200, 'duration': 120}
            },
            'S2': {
                'flow_1': {'packets': 12456, 'bytes': 14947200, 'duration': 120}
            }
        }
        
        total_packets = sum(
            f['packets'] for switch in self.flow_stats.values() 
            for f in switch.values()
        )
        total_bytes = sum(
            f['bytes'] for switch in self.flow_stats.values() 
            for f in switch.values()
        )
        
        print(f"   ✓ Total packets: {total_packets:,}")
        print(f"   ✓ Total bytes: {total_bytes:,}")
        print(f"   ✓ Average throughput: {(total_bytes * 8 / 120 / 1000000):.2f} Mbps")
    
    def _simulate_qos(self):
        """Simulate QoS policy application."""
        self.qos_policies = {
            'voip': {
                'priority': 'high',
                'match': {'ip_proto': 17, 'udp_dst': 5060},
                'action': 'queue:1'
            },
            'video': {
                'priority': 'high',
                'match': {'ip_proto': 17, 'udp_dst': 554},
                'action': 'queue:1'
            },
            'web': {
                'priority': 'medium',
                'match': {'ip_proto': 6, 'tcp_dst': 80},
                'action': 'queue:2'
            }
        }
        
        print(f"   ✓ Applied {len(self.qos_policies)} QoS policies")
        for name, policy in self.qos_policies.items():
            print(f"     - {name}: Priority={policy['priority']}")
    
    def _simulate_load_balancer(self):
        """Simulate load balancer configuration."""
        self.load_balancer = {
            'enabled': True,
            'virtual_ip': '10.0.0.100',
            'servers': [
                {'ip': '10.0.0.2', 'weight': 1, 'connections': 0},
                {'ip': '10.0.0.3', 'weight': 1, 'connections': 0}
            ],
            'algorithm': 'round_robin'
        }
        
        print(f"   ✓ Virtual IP: {self.load_balancer['virtual_ip']}")
        print(f"   ✓ Backend servers: {len(self.load_balancer['servers'])}")
        print(f"   ✓ Algorithm: {self.load_balancer['algorithm']}")
    
    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        """
        Add a flow entry to the switch.
        
        Args:
            datapath: Switch datapath
            priority: Flow priority
            match: Match criteria
            actions: Actions to perform
            buffer_id: Buffer ID (optional)
            idle_timeout: Idle timeout in seconds
            hard_timeout: Hard timeout in seconds
        """
        if not RYU_AVAILABLE:
            logger.info(f"[SIMULATION] Adding flow: priority={priority}")
            return
        
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath=datapath, buffer_id=buffer_id, priority=priority,
                match=match, instructions=inst, idle_timeout=idle_timeout,
                hard_timeout=hard_timeout
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath, priority=priority, match=match,
                instructions=inst, idle_timeout=idle_timeout,
                hard_timeout=hard_timeout
            )
        
        datapath.send_msg(mod)
    
    def get_topology(self):
        """Get current network topology."""
        return self.topology
    
    def get_stats(self):
        """Get traffic statistics."""
        return {
            'flow_stats': dict(self.flow_stats),
            'port_stats': dict(self.port_stats),
            'timestamp': datetime.now().isoformat()
        }
    
    def set_qos_policy(self, name, priority, match, action):
        """
        Set a QoS policy.
        
        Args:
            name: Policy name
            priority: Priority level (high, medium, low)
            match: Traffic match criteria
            action: Action to apply
        """
        self.qos_policies[name] = {
            'priority': priority,
            'match': match,
            'action': action
        }
        logger.info(f"QoS policy '{name}' added with priority '{priority}'")
        return True
    
    def configure_load_balancer(self, virtual_ip, servers, algorithm='round_robin'):
        """
        Configure the load balancer.
        
        Args:
            virtual_ip: Virtual IP address
            servers: List of backend server IPs
            algorithm: Load balancing algorithm
        """
        self.load_balancer = {
            'enabled': True,
            'virtual_ip': virtual_ip,
            'servers': [{'ip': s, 'weight': 1, 'connections': 0} for s in servers],
            'algorithm': algorithm,
            'current_index': 0
        }
        logger.info(f"Load balancer configured: VIP={virtual_ip}, Servers={servers}")
        return True
    
    def get_next_server(self):
        """Get the next server for load balancing."""
        if not self.load_balancer['enabled'] or not self.load_balancer['servers']:
            return None
        
        if self.load_balancer['algorithm'] == 'round_robin':
            server = self.load_balancer['servers'][self.load_balancer['current_index']]
            self.load_balancer['current_index'] = (
                (self.load_balancer['current_index'] + 1) % 
                len(self.load_balancer['servers'])
            )
            return server['ip']
        
        return self.load_balancer['servers'][0]['ip']


# Ryu Application (only if Ryu is available)
if RYU_AVAILABLE:
    class RyuSDNController(app_manager.RyuApp):
        """Ryu SDN Controller Application."""
        
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
        
        def __init__(self, *args, **kwargs):
            super(RyuSDNController, self).__init__(*args, **kwargs)
            self.controller = SDNController()
            self.mac_to_port = {}
            self.datapaths = {}
            
            # Start monitoring thread
            self.monitor_thread = hub.spawn(self._monitor)
        
        @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
        def switch_features_handler(self, ev):
            """Handle switch connection."""
            datapath = ev.msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            
            self.datapaths[datapath.id] = datapath
            self.logger.info(f"Switch connected: {datapath.id}")
            
            # Install table-miss flow entry
            match = parser.OFPMatch()
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(datapath, 0, match, actions)
        
        @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
        def packet_in_handler(self, ev):
            """Handle packet-in events."""
            msg = ev.msg
            datapath = msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            in_port = msg.match['in_port']
            
            pkt = packet.Packet(msg.data)
            eth = pkt.get_protocols(ethernet.ethernet)[0]
            
            dst = eth.dst
            src = eth.src
            dpid = datapath.id
            
            # Learn MAC address
            self.mac_to_port.setdefault(dpid, {})
            self.mac_to_port[dpid][src] = in_port
            
            # Determine output port
            if dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][dst]
            else:
                out_port = ofproto.OFPP_FLOOD
            
            actions = [parser.OFPActionOutput(out_port)]
            
            # Install flow if we know the destination
            if out_port != ofproto.OFPP_FLOOD:
                match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
                self.add_flow(datapath, 1, match, actions)
            
            # Send packet out
            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data
            
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id,
                in_port=in_port, actions=actions, data=data
            )
            datapath.send_msg(out)
        
        def add_flow(self, datapath, priority, match, actions, buffer_id=None):
            """Add a flow entry."""
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
            
            if buffer_id:
                mod = parser.OFPFlowMod(
                    datapath=datapath, buffer_id=buffer_id, priority=priority,
                    match=match, instructions=inst
                )
            else:
                mod = parser.OFPFlowMod(
                    datapath=datapath, priority=priority, match=match, instructions=inst
                )
            
            datapath.send_msg(mod)
        
        def _monitor(self):
            """Monitor thread for collecting statistics."""
            while True:
                for dp in self.datapaths.values():
                    self._request_stats(dp)
                hub.sleep(10)
        
        def _request_stats(self, datapath):
            """Request flow statistics from switch."""
            parser = datapath.ofproto_parser
            req = parser.OFPFlowStatsRequest(datapath)
            datapath.send_msg(req)
        
        @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
        def flow_stats_reply_handler(self, ev):
            """Handle flow statistics reply."""
            body = ev.msg.body
            dpid = ev.msg.datapath.id
            
            for stat in sorted([flow for flow in body], 
                              key=lambda f: f.priority, reverse=True):
                self.controller.flow_stats[dpid][stat.cookie] = {
                    'packets': stat.packet_count,
                    'bytes': stat.byte_count,
                    'duration': stat.duration_sec
                }
