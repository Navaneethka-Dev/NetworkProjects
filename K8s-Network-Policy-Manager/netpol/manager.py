#!/usr/bin/env python3
"""
Kubernetes Network Policy Manager - Main Module
Orchestrates policy management operations.

Author: Navaneethraj KA
"""

import os
from typing import Dict, List, Optional, Any

# Try to import kubernetes client
try:
    from kubernetes import client, config
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False


class NetworkPolicyManager:
    """Main class for managing Kubernetes Network Policies."""
    
    def __init__(self, kubeconfig: str = None):
        """Initialize the manager."""
        self.k8s_client = None
        
        if K8S_AVAILABLE:
            try:
                if kubeconfig:
                    config.load_kube_config(config_file=kubeconfig)
                else:
                    config.load_kube_config()
                self.k8s_client = client.NetworkingV1Api()
            except:
                pass
    
    def list_policies(self, namespace: str = 'default') -> List[Dict]:
        """List network policies in a namespace."""
        policies = []
        
        if self.k8s_client:
            try:
                result = self.k8s_client.list_namespaced_network_policy(namespace)
                for item in result.items:
                    policies.append({
                        'name': item.metadata.name,
                        'namespace': item.metadata.namespace,
                        'pod_selector': item.spec.pod_selector.match_labels or {},
                        'policy_types': item.spec.policy_types or ['Ingress']
                    })
            except Exception as e:
                print(f"Error listing policies: {e}")
        else:
            # Demo data
            policies = [
                {'name': 'default-deny', 'namespace': namespace, 
                 'pod_selector': {}, 'policy_types': ['Ingress', 'Egress']},
                {'name': 'allow-web', 'namespace': namespace,
                 'pod_selector': {'app': 'web'}, 'policy_types': ['Ingress']},
            ]
        
        return policies
    
    def generate_deny_all(self, namespace: str = 'default', 
                          name: str = None) -> Dict:
        """Generate a default deny-all policy."""
        return {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'NetworkPolicy',
            'metadata': {
                'name': name or 'default-deny-all',
                'namespace': namespace
            },
            'spec': {
                'podSelector': {},
                'policyTypes': ['Ingress', 'Egress']
            }
        }
    
    def generate_allow_dns(self, namespace: str = 'default',
                           name: str = None) -> Dict:
        """Generate an allow-DNS policy."""
        return {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'NetworkPolicy',
            'metadata': {
                'name': name or 'allow-dns',
                'namespace': namespace
            },
            'spec': {
                'podSelector': {},
                'policyTypes': ['Egress'],
                'egress': [{
                    'to': [{'namespaceSelector': {
                        'matchLabels': {'kubernetes.io/metadata.name': 'kube-system'}
                    }}],
                    'ports': [{'protocol': 'UDP', 'port': 53}]
                }]
            }
        }
    
    def generate_allow_web(self, namespace: str = 'default',
                           name: str = None) -> Dict:
        """Generate an allow-web ingress policy."""
        return {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'NetworkPolicy',
            'metadata': {
                'name': name or 'allow-web-ingress',
                'namespace': namespace
            },
            'spec': {
                'podSelector': {'matchLabels': {'app': 'web'}},
                'policyTypes': ['Ingress'],
                'ingress': [{
                    'from': [{'namespaceSelector': {}}],
                    'ports': [
                        {'protocol': 'TCP', 'port': 80},
                        {'protocol': 'TCP', 'port': 443}
                    ]
                }]
            }
        }
    
    def validate(self, policy: Dict) -> List[Dict]:
        """Validate a network policy."""
        issues = []
        
        # Check required fields
        if policy.get('apiVersion') != 'networking.k8s.io/v1':
            issues.append({'severity': 'high', 
                          'message': 'Invalid or missing apiVersion'})
        
        if policy.get('kind') != 'NetworkPolicy':
            issues.append({'severity': 'high', 
                          'message': 'Kind must be NetworkPolicy'})
        
        spec = policy.get('spec', {})
        
        # Check for overly permissive rules
        if spec.get('ingress') == [{}]:
            issues.append({'severity': 'high',
                          'message': 'Policy allows ALL ingress traffic'})
        
        if spec.get('egress') == [{}]:
            issues.append({'severity': 'medium',
                          'message': 'Policy allows ALL egress traffic'})
        
        # Check for empty pod selector with allow rules
        if not spec.get('podSelector', {}).get('matchLabels'):
            if spec.get('ingress') or spec.get('egress'):
                issues.append({'severity': 'medium',
                              'message': 'Empty podSelector applies to all pods'})
        
        return issues
    
    def audit(self, namespace: str = 'default') -> Dict:
        """Audit policies in a namespace."""
        policies = self.list_policies(namespace)
        findings = []
        score = 100
        
        # Check for default deny
        has_deny_all = any(
            not p['pod_selector'] and 'Egress' in p['policy_types']
            for p in policies
        )
        
        if not has_deny_all:
            findings.append({
                'severity': 'high',
                'rule': 'deny-by-default',
                'message': 'No default deny policy found'
            })
            score -= 30
        
        # Check policy coverage
        if len(policies) < 2:
            findings.append({
                'severity': 'medium',
                'rule': 'policy-coverage',
                'message': 'Limited network policy coverage'
            })
            score -= 15
        
        return {
            'namespace': namespace,
            'policy_count': len(policies),
            'score': max(0, score),
            'findings': findings,
            'policies': policies
        }
    
    def apply(self, policy: Dict, dry_run: bool = False) -> Dict:
        """Apply a network policy."""
        name = policy.get('metadata', {}).get('name', 'unknown')
        namespace = policy.get('metadata', {}).get('namespace', 'default')
        
        if dry_run:
            return {'success': True, 'name': name, 'dry_run': True}
        
        if self.k8s_client:
            try:
                self.k8s_client.create_namespaced_network_policy(
                    namespace=namespace, body=policy)
                return {'success': True, 'name': name}
            except Exception as e:
                return {'success': False, 'name': name, 'error': str(e)}
        
        return {'success': True, 'name': name, 'simulated': True}
    
    def visualize(self, namespace: str, output: str) -> bool:
        """Generate network policy visualization."""
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            
            policies = self.list_policies(namespace)
            if not policies:
                return False
            
            G = nx.DiGraph()
            
            # Add nodes for each policy
            for p in policies:
                G.add_node(p['name'], type='policy')
                selector = p.get('pod_selector', {})
                if selector:
                    label = ','.join(f"{k}={v}" for k, v in selector.items())
                    G.add_node(label, type='pods')
                    G.add_edge(p['name'], label)
            
            # Draw graph
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G)
            
            policy_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'policy']
            pod_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'pods']
            
            nx.draw_networkx_nodes(G, pos, nodelist=policy_nodes, 
                                   node_color='lightblue', node_size=2000)
            nx.draw_networkx_nodes(G, pos, nodelist=pod_nodes,
                                   node_color='lightgreen', node_size=1500)
            nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True)
            nx.draw_networkx_labels(G, pos, font_size=8)
            
            plt.title(f'Network Policies: {namespace}')
            plt.axis('off')
            plt.savefig(output, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except ImportError:
            print("matplotlib/networkx not installed for visualization")
            return False
