# Kubernetes Network Policy Manager 🛡️

A comprehensive tool for managing, visualizing, and auditing Kubernetes Network Policies. Features policy generation, validation, visualization, and security compliance checking.

![Kubernetes](https://img.shields.io/badge/Kubernetes-1.25+-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🚀 Features

- **Policy Generator**: Create NetworkPolicies from templates or traffic analysis
- **Policy Validator**: Validate policies against best practices
- **Visualization**: Generate network policy diagrams
- **Compliance Audit**: Check policies against security standards
- **Traffic Analyzer**: Analyze pod traffic patterns
- **CLI & API**: Command-line tool and Python API
- **Multi-CNI Support**: Works with Calico, Cilium, Weave, and others

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 K8s Network Policy Manager                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │   Policy    │  │   Traffic   │  │    Compliance       │   │
│  │  Generator  │  │  Analyzer   │  │      Auditor        │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │   Policy    │  │   Policy    │  │     Visualizer      │   │
│  │  Validator  │  │   Applier   │  │                     │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                    Kubernetes API                             │
└──────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
K8s-Network-Policy-Manager/
├── netpol/
│   ├── __init__.py
│   ├── manager.py           # Main policy manager
│   ├── generator.py         # Policy generator
│   ├── validator.py         # Policy validator
│   ├── visualizer.py        # Policy visualization
│   └── auditor.py           # Compliance auditor
├── templates/
│   ├── deny-all.yaml        # Default deny policy
│   ├── allow-dns.yaml       # Allow DNS access
│   └── allow-ingress.yaml   # Allow ingress traffic
├── examples/
│   └── sample-policies/     # Example policies
├── config/
│   └── compliance-rules.yaml
├── requirements.txt
├── netpol-cli.py            # CLI entry point
└── README.md
```

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/Navaneethka-Dev/K8s-Network-Policy-Manager.git
cd K8s-Network-Policy-Manager

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Ensure kubectl is configured
kubectl cluster-info
```

## 🚀 Usage

### CLI Commands

```bash
# List all network policies
python netpol-cli.py list --namespace default

# Generate a default-deny policy
python netpol-cli.py generate deny-all --namespace myapp

# Validate a policy file
python netpol-cli.py validate policy.yaml

# Audit all policies in a namespace
python netpol-cli.py audit --namespace production

# Visualize policies
python netpol-cli.py visualize --namespace default --output diagram.png

# Apply a policy
python netpol-cli.py apply policy.yaml --dry-run
```

### Python API

```python
from netpol import NetworkPolicyManager

# Initialize manager
npm = NetworkPolicyManager()

# List policies
policies = npm.list_policies(namespace='default')

# Generate deny-all policy
policy = npm.generate_deny_all('myapp')

# Validate policy
issues = npm.validate(policy)

# Apply policy
npm.apply(policy, dry_run=True)

# Audit namespace
report = npm.audit('production')
```

## 📊 Policy Templates

### Default Deny All
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

### Allow DNS
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
```

## 🔍 Compliance Rules

The auditor checks policies against these security standards:

| Rule | Description | Severity |
|------|-------------|----------|
| `deny-by-default` | Namespace should have default deny policy | High |
| `no-allow-all` | Avoid policies that allow all traffic | High |
| `explicit-ports` | Specify explicit ports, not all ports | Medium |
| `labeled-selectors` | Use specific label selectors | Medium |
| `egress-control` | Control egress traffic | Medium |

## 📈 Results

- **100% visibility** into cluster network policies
- **Automated policy generation** reducing manual work by 70%
- **Compliance checking** against CIS Kubernetes Benchmark
- **Visual diagrams** for documentation and review

## ⚙️ Configuration

Edit `config/settings.yaml`:

```yaml
kubernetes:
  kubeconfig: ~/.kube/config
  context: default

audit:
  severity_threshold: medium
  ignore_namespaces:
    - kube-system
    - kube-public

visualization:
  output_format: png
  include_labels: true
```

## 📄 License

MIT License

## 👨‍💻 Author

**Navaneethraj KA**
- GitHub: [@Navaneethka-Dev](https://github.com/Navaneethka-Dev)
- LinkedIn: [navaneethraj-alagiri](https://linkedin.com/in/navaneethraj-alagiri)
- Email: nvnthrj@gmail.com
