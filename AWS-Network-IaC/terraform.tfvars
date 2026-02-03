# Terraform Variables - Customize for your deployment
# Author: Navaneethraj KA

# Project Settings
project_name = "prod-network"
environment  = "production"

# AWS Settings
aws_region = "ap-south-1"

# Network Settings
vpc_cidr = "10.0.0.0/16"
az_count = 2

# Feature Toggles
enable_nat_gateway = true
enable_flow_logs   = true
enable_alb         = true
alb_internal       = false

# Access Control
allowed_ssh_cidrs  = []              # Add your IP for SSH access
allowed_http_cidrs = ["0.0.0.0/0"]   # Restrict in production
