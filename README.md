# Medical Research Citation Finder

A microservices-based system for processing medical research papers, providing intelligent search and summarization capabilities using RAG (Retrieval Augmented Generation).

## Project Overview

This system:
- Processes medical research papers from PubMed
- Uses RAG for intelligent searching
- Provides summarization using T5
- Built as microservices on DigitalOcean

## Prerequisites

- DigitalOcean account
- doctl CLI
- kubectl
- Terraform
- Python 3.9+
- Docker and Docker Compose

## Initial Setup

1. **Install Required Tools**
   ```bash
   # Install doctl
   brew install doctl

   # Install terraform
   brew install terraform

   # Install kubectl
   brew install kubernetes-cli
   ```

2. **DigitalOcean Configuration**
   ```bash
   # Generate Personal Access Token (PAT) from DO dashboard
   # https://cloud.digitalocean.com/account/api/tokens
   
   # Authenticate doctl
   doctl auth init -t your-token

   # Generate Spaces credentials
   # Go to DO dashboard → API → Spaces keys
   ```

3. **Infrastructure Setup**
   ```bash
   # Navigate to terraform directory
   cd infrastructure/terraform

   # Initialize terraform
   terraform init

   # Apply configuration
   terraform apply
   ```

## Infrastructure Components

### Current Setup
- **Kubernetes Cluster (DOKS)**
  - Region: SFO3
  - Version: 1.29.9-do.4
  - Node Pool: 2 nodes (s-2vcpu-4gb)

- **PostgreSQL Database**
  - Version: 15
  - Size: db-s-1vcpu-1gb
  - Region: SFO3

- **Spaces Bucket**
  - Name: citation-finder-documents
  - Region: SFO3

### Accessing Resources

1. **Kubernetes Cluster**
   ```bash
   # Get cluster access
   doctl kubernetes cluster kubeconfig save citation-finder-cluster
   
   # Verify connection
   kubectl get nodes
   ```

2. **Database**
   ```bash
   # List databases
   doctl databases list
   
   # Get connection info (replace with your DB ID)
   doctl databases get YOUR_DB_ID
   ```

3. **Spaces**
   ```bash
   # Configure s3cmd for Spaces access
   s3cmd --configure
   
   # List buckets
   s3cmd ls
   ```

## Project Structure
```
citation-finder/
├── .github/workflows/      # CI/CD configurations
├── infrastructure/         # Infrastructure as Code
│   ├── terraform/         # Terraform configurations
│   └── k8s/              # Kubernetes manifests
├── services/              # Microservices
│   ├── data-ingestion/    # PubMed data ingestion
│   ├── document-processor/# Document processing
│   ├── rag-service/      # RAG implementation
│   └── api-gateway/      # API Gateway
├── docker/               # Docker configurations
├── config/               # Configuration files
├── scripts/              # Utility scripts
└── docs/                # Documentation
```

## Next Steps
1. Configure Kubernetes secrets and configs
2. Deploy microservices
3. Set up monitoring
4. Configure CI/CD pipelines

## Common Issues and Solutions

1. **Token Authentication Issues**
   ```bash
   doctl auth init -t your-token
   ```

2. **Kubernetes Version Mismatch**
   ```bash
   # Check available versions
   doctl kubernetes options versions
   ```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Submit a pull request

## License

[Add your license here]

## Team

- DevOps Engineers: Karthikeya Vanguru, Rakshit Gade
- Database Admin: Tanya Sharma
- ML Engineer: Srikar Madipalli