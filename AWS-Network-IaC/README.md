# AWS Network Infrastructure as Code 🌩️

Production-grade AWS network infrastructure deployment using Terraform. Features multi-AZ VPC architecture with public/private subnets, NAT Gateways, Application Load Balancer, and Security Groups.

![Terraform](https://img.shields.io/badge/Terraform-1.0+-purple.svg)
![AWS](https://img.shields.io/badge/AWS-Cloud-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🏗️ Architecture

```
                                    ┌──────────────────────────────────────────┐
                                    │              AWS CLOUD                    │
                                    │                                          │
┌─────────────┐                     │  ┌────────────────────────────────────┐  │
│   Internet  │◄───────────────────►│  │         Application Load           │  │
│   Gateway   │                     │  │           Balancer (ALB)            │  │
└─────────────┘                     │  └────────────────────────────────────┘  │
                                    │              │                │          │
                                    │              ▼                ▼          │
                                    │  ┌────────────────┐  ┌────────────────┐  │
                                    │  │  Public Subnet │  │  Public Subnet │  │
                                    │  │     AZ-1a      │  │     AZ-1b      │  │
                                    │  │   10.0.1.0/24  │  │   10.0.2.0/24  │  │
                                    │  └────────────────┘  └────────────────┘  │
                                    │         │                    │           │
                                    │         ▼                    ▼           │
                                    │  ┌────────────────┐  ┌────────────────┐  │
                                    │  │   NAT Gateway  │  │   NAT Gateway  │  │
                                    │  └────────────────┘  └────────────────┘  │
                                    │         │                    │           │
                                    │         ▼                    ▼           │
                                    │  ┌────────────────┐  ┌────────────────┐  │
                                    │  │ Private Subnet │  │ Private Subnet │  │
                                    │  │     AZ-1a      │  │     AZ-1b      │  │
                                    │  │   10.0.3.0/24  │  │   10.0.4.0/24  │  │
                                    │  │  ┌──────────┐  │  │  ┌──────────┐  │  │
                                    │  │  │   EC2    │  │  │  │   EC2    │  │  │
                                    │  │  │ Instance │  │  │  │ Instance │  │  │
                                    │  │  └──────────┘  │  │  └──────────┘  │  │
                                    │  └────────────────┘  └────────────────┘  │
                                    │                                          │
                                    └──────────────────────────────────────────┘
```

## 📁 Project Structure

```
AWS-Network-IaC/
├── main.tf                 # Main infrastructure configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── providers.tf            # Provider configuration
├── vpc.tf                  # VPC and subnet configurations
├── security_groups.tf      # Security group rules
├── alb.tf                  # Application Load Balancer
├── nat_gateway.tf          # NAT Gateway configuration
├── route_tables.tf         # Route table configurations
├── terraform.tfvars        # Variable values (customize this)
├── modules/
│   └── vpc/               # Reusable VPC module
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── README.md
```

## 🚀 Features

- ✅ **Multi-AZ Deployment**: High availability across 2 availability zones
- ✅ **Public/Private Subnets**: Proper network segmentation
- ✅ **NAT Gateways**: Secure outbound internet access for private subnets
- ✅ **Application Load Balancer**: HTTPS-ready load balancing
- ✅ **Security Groups**: Least-privilege access controls
- ✅ **Flow Logs**: VPC flow logging for security monitoring
- ✅ **Tagging**: Consistent resource tagging for cost management

## 🛠️ Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- AWS account with appropriate permissions

## ⚙️ Usage

### 1. Clone the Repository

```bash
git clone https://github.com/Navaneethka-Dev/AWS-Network-IaC.git
cd AWS-Network-IaC
```

### 2. Configure Variables

Edit `terraform.tfvars` with your settings:

```hcl
project_name    = "my-network"
environment     = "production"
aws_region      = "ap-south-1"
vpc_cidr        = "10.0.0.0/16"
```

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Plan the Deployment

```bash
terraform plan
```

### 5. Apply the Configuration

```bash
terraform apply
```

### 6. Destroy (when needed)

```bash
terraform destroy
```

## 📊 Outputs

After deployment, Terraform will output:

| Output | Description |
|--------|-------------|
| `vpc_id` | The ID of the created VPC |
| `public_subnet_ids` | List of public subnet IDs |
| `private_subnet_ids` | List of private subnet IDs |
| `alb_dns_name` | DNS name of the Application Load Balancer |
| `nat_gateway_ips` | Elastic IPs of NAT Gateways |

## 💰 Cost Estimation

| Resource | Estimated Monthly Cost |
|----------|----------------------|
| NAT Gateway (2x) | ~$65/month |
| ALB | ~$16/month |
| VPC/Subnets | Free |
| Security Groups | Free |
| **Total** | **~$81/month** |

## 🔒 Security Features

- Private subnets with no direct internet access
- NAT Gateway for controlled outbound traffic
- Security groups with minimal required ports
- VPC Flow Logs for traffic monitoring
- No default security group rules

## 📈 Results

- **99.9% uptime** with Multi-AZ architecture
- **Reduced latency** with regional deployment
- **Secure by design** with private subnets
- **Infrastructure as Code** for version control and reproducibility

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 👨‍💻 Author

**Navaneethraj KA**
- GitHub: [@Navaneethka-Dev](https://github.com/Navaneethka-Dev)
- LinkedIn: [navaneethraj-alagiri](https://linkedin.com/in/navaneethraj-alagiri)
- Email: nvnthrj@gmail.com
