# Network Monitoring Dashboard 📊

A real-time network monitoring dashboard built with Python, Flask, and Dash. Monitors network devices via SNMP, displays live metrics, alerts on anomalies, and provides historical data visualization.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-Web-green.svg)
![Dash](https://img.shields.io/badge/Dash-Plotly-orange.svg)

## 🚀 Features

- **Real-time Monitoring**: Live device status and metrics
- **SNMP Integration**: Automatic device discovery and polling
- **Interactive Dashboards**: Plotly-powered visualizations
- **Alerting System**: Email and webhook notifications
- **Multi-Protocol Support**: SNMP v1/v2c/v3, ICMP, TCP
- **Historical Data**: Time-series storage and analysis
- **Device Management**: Add, edit, and organize devices
- **Customizable Widgets**: Build your own dashboard layouts

## 📸 Dashboard Preview

```
┌─────────────────────────────────────────────────────────────────┐
│  🌐 Network Monitor Dashboard                    🔔 2 Alerts    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Devices   │  │   Uptime    │  │  Bandwidth  │             │
│  │     24      │  │   99.8%     │  │   2.4 Gbps  │             │
│  │   Online    │  │   Overall   │  │   Total     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Traffic Graph (Last 24 Hours)                         │    │
│  │  ████████████████████████                              │    │
│  │  ██████████████████                                    │    │
│  │  ████████████                                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌──────────────────────┐  ┌────────────────────────────┐      │
│  │ Device Status        │  │ Top Talkers               │      │
│  │ ● Router-1    OK     │  │ 192.168.1.10   1.2 Gbps   │      │
│  │ ● Switch-1    OK     │  │ 192.168.1.20   800 Mbps   │      │
│  │ ● Firewall    OK     │  │ 192.168.1.30   400 Mbps   │      │
│  │ ○ AP-Floor2   DOWN   │  │                           │      │
│  └──────────────────────┘  └────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
Network-Monitor-Dashboard/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Flask application
│   ├── dashboard.py            # Dash dashboard
│   ├── models.py               # Database models
│   ├── snmp_poller.py          # SNMP polling engine
│   ├── alerting.py             # Alert management
│   └── api.py                  # REST API endpoints
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── dashboard.js
├── templates/
│   ├── base.html
│   ├── index.html
│   └── devices.html
├── config/
│   └── settings.yaml
├── data/
│   └── network.db              # SQLite database
├── requirements.txt
├── run.py
└── README.md
```

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/Navaneethka-Dev/Network-Monitor-Dashboard.git
cd Network-Monitor-Dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app.models import init_db; init_db()"

# Run the application
python run.py
```

## 🌐 Access the Dashboard

Open your browser and navigate to `http://localhost:5000`

## ⚙️ Configuration

Edit `config/settings.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 5000
  debug: false

snmp:
  community: "public"
  version: "2c"
  timeout: 5
  retries: 3

polling:
  interval: 60  # seconds
  threads: 10

alerting:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
```

## 📊 Monitored Metrics

| Metric | Description | SNMP OID |
|--------|-------------|----------|
| CPU Usage | Processor utilization | 1.3.6.1.4.1.9.2.1.56.0 |
| Memory | RAM usage percentage | 1.3.6.1.4.1.9.9.48.1.1.1.5 |
| Interface Traffic | In/Out bytes | 1.3.6.1.2.1.2.2.1.10/16 |
| Interface Status | Up/Down state | 1.3.6.1.2.1.2.2.1.8 |
| Uptime | System uptime | 1.3.6.1.2.1.1.3.0 |

## 📈 Results

- **24/7 real-time monitoring** of network infrastructure
- **50+ devices** monitored simultaneously
- **< 1 minute** alert notification time
- **30-day** historical data retention

## 📄 License

MIT License

## 👨‍💻 Author

**Navaneethraj KA**
- GitHub: [@Navaneethka-Dev](https://github.com/Navaneethka-Dev)
- LinkedIn: [navaneethraj-alagiri](https://linkedin.com/in/navaneethraj-alagiri)
- Email: nvnthrj@gmail.com
