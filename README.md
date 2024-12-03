# Medical Research Citation Finder

A microservices-based system for processing medical research papers using RAG (Retrieval Augmented Generation) for intelligent searching and summarization.

## System Architecture

### Components Overview
```
                                   ┌─────────────────┐
                                   │   API Gateway   │
                                   └────────┬────────┘
                                           │
                 ┌───────────────────┬─────┴─────┬───────────────────┐
                 │                   │           │                   │
        ┌────────┴────────┐ ┌───────┴───────┐   │           ┌───────┴───────┐
        │  Data Ingestion │ │ Doc Processor │   │           │   RAG Service │
        └────────┬────────┘ └───────┬───────┘   │           └───────┬───────┘
                 │                  │       ┌────┴────┐             │
                 │                  │       │ MLflow  │             │
        ┌────────┴────────┐        │       └────┬────┘     ┌───────┴───────┐
        │    PubMed API   │   ┌────┴────┐       │         │    T5 Model   │
        └─────────────────┘   │  Spaces │       │         └───────────────┘
                             └────┬────┘  ┌─────┴─────┐
                                  │       │ PostgreSQL │
                                  │       │ (pgvector) │
                                  └───────┴───────────┘
```

## Technical Requirements

### System Requirements
- CPU: Minimum 4 cores recommended
- RAM: Minimum 8GB (16GB recommended for ML components)
- Storage: 20GB+ for model storage and document cache
- GPU: Optional, but recommended for T5 model inference

### Software Requirements
```bash
# Core Requirements
Python 3.9 (exact version required for compatibility)
Docker 24.0.0+
kubectl 1.29+
Terraform 1.6+
doctl 1.101+

# Python Libraries
fastapi==0.104.1
llama-index==0.9.3
torch==2.1.1
transformers==4.35.2
psycopg2-binary==2.9.9
mlflow==2.8.1
```

## Quick Start Guide

### 1. Initial Setup

```bash
# Clone repository
git clone [repo-url]
cd citation-finder

# Create Python virtual environment
python3.9 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install development tools
brew install doctl kubectl terraform  # For macOS
```

### 2. DigitalOcean Setup

```bash
# Configure doctl
doctl auth init  # Enter your DO access token

# Set up Kubernetes cluster access
doctl kubernetes cluster kubeconfig save citation-finder-cluster

# Verify cluster access
kubectl get nodes
```

### 3. Infrastructure Setup

```bash
# Initialize Terraform
cd infrastructure/terraform
terraform init

# Review and apply infrastructure
terraform plan
terraform apply

# Verify resources
doctl kubernetes cluster list
doctl databases list
```

### 4. Development Environment

```bash
# Set up environment variables
cp config/environments/example.env config/environments/dev.env

# Required environment variables:
PUBMED_API_KEY=your_key
POSTGRES_URI=your_uri
MLFLOW_TRACKING_URI=http://mlflow:5000
DO_SPACES_KEY=your_key
DO_SPACES_SECRET=your_secret
```

## Service Development

### Data Ingestion Service
```bash
# Setup PubMed API access
# 1. Get API key from: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
# 2. Add to Kubernetes secrets:
kubectl create secret generic pubmed-credentials \
  --from-literal=PUBMED_API_KEY=your_key \
  -n citation-finder

# Local development
cd services/data-ingestion
uvicorn src.main:app --reload
```

### Document Processor Service
```bash
# Required for document processing
pip install python-magic pdf2image

# Setup DO Spaces
# Configure in infrastructure/k8s/base/spaces-secret.yaml
```

### RAG Service
```bash
# T5 Model Setup
# Download model (will be cached)
python -c "from transformers import T5ForConditionalGeneration, T5Tokenizer; \
          model = T5ForConditionalGeneration.from_pretrained('google/flan-t5-base'); \
          tokenizer = T5Tokenizer.from_pretrained('google/flan-t5-base')"

# Setup vector database
# 1. Enable pgvector:
psql "postgresql://doadmin:pass@host:port/defaultdb?sslmode=require" -c 'CREATE EXTENSION vector;'
```

### MLflow Setup
```bash
# Deploy MLflow
kubectl apply -f infrastructure/k8s/base/mlflow.yaml

# Access MLflow UI
kubectl port-forward svc/mlflow 5000:5000 -n citation-finder
```

## Database Management

### pgvector Setup
```sql
-- Connect to database
\c defaultdb

-- Create extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    pmid TEXT UNIQUE NOT NULL,
    title TEXT,
    abstract TEXT,
    embedding vector(384)  -- Dimension matches your model
);
```

## Testing

### Unit Tests
```bash
# Run all tests
make test

# Run specific service tests
cd services/data-ingestion
pytest

# Run with coverage
pytest --cov=src tests/
```

### Integration Tests
```bash
# Start integration test environment
docker-compose -f docker/docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration
```

## Deployment

### Build and Push Services
```bash
# Login to DO registry
doctl registry login

# Build all services
make build-all

# Push all services
make push-all

# Or for specific service:
make build-push SERVICE=data-ingestion
```

### Deploy to Kubernetes
```bash
# Apply base configurations
kubectl apply -f infrastructure/k8s/base/

# Deploy specific service
kubectl apply -f infrastructure/k8s/base/data-ingestion.yaml

# Verify deployment
kubectl get pods -n citation-finder
```

## Monitoring and Logging

### Setup Monitoring
```bash
# Deploy monitoring stack
kubectl apply -f infrastructure/k8s/monitoring/

# Access Grafana
kubectl port-forward svc/grafana 3000:3000 -n monitoring
```

### Access Logs
```bash
# View service logs
kubectl logs -f -l app=data-ingestion -n citation-finder

# View MLflow logs
kubectl logs -f -l app=mlflow -n citation-finder
```

## Troubleshooting

### Common Issues

1. Model Loading Issues
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Verify model cache
ls ~/.cache/huggingface/
```

2. Database Connection Issues
```bash
# Test connection
psql "postgresql://doadmin:pass@host:port/defaultdb?sslmode=require"

# Check vector extension
\dx
```

3. Memory Issues
```bash
# Check node resources
kubectl describe node

# View pod resource usage
kubectl top pod -n citation-finder
```

## Team Workflow

### Development Process
1. Create feature branch from main
2. Implement changes
3. Add tests
4. Update documentation
5. Create PR
6. Get review
7. Merge

### Code Review Guidelines
- Check for proper error handling
- Verify resource cleanup
- Ensure proper logging
- Check for security best practices
- Verify documentation updates

## Resources

- [Project Documentation](./docs/)
- [API Documentation](./docs/api/)
- [Architecture Guide](./docs/architecture/)
- [Deployment Guide](./docs/deployment/)
- [Contributing Guide](./CONTRIBUTING.md)

## Security Notes

- All credentials must be stored in Kubernetes secrets
- Enable network policies
- Regular security updates
- Access logging enabled
- Regular security audits


# TEAM TASK DISTRIBUTION

## Karthikeya Vanguru (DevOps Engineer)
Focus: Infrastructure and CI/CD
Tasks:
1. GitHub Actions setup
   - CI pipeline for testing
   - CD pipeline for deployment
2. Kubernetes configurations
   - Service mesh setup
   - Network policies
3. Monitoring setup
   - Prometheus/Grafana
   - Logging infrastructure

## Rakshit Gade (DevOps Engineer)
Focus: Service Deployment and Security
Tasks:
1. Service deployment configurations
   - Helm charts
   - Resource management
2. Security implementations
   - Secret management
   - Service authentication
3. Load balancing and scaling
   - Ingress configurations
   - Auto-scaling policies

## Tanya Sharma (Database Admin)
Focus: Database and Storage
Tasks:
1. Database setup
   - pgvector implementation
   - Schema design and optimization
2. Data migration scripts
   - Backup strategies
   - Recovery procedures
3. Storage optimization
   - DO Spaces configuration
   - Document storage strategies

## Srikar Madipalli (ML Engineer)
Focus: ML Implementation and Integration
Tasks:
1. RAG service implementation
   - Llama-index integration
   - T5 model implementation
2. MLflow setup
   - Model tracking
   - Experiment management
3. Model optimization
   - Performance tuning
   - Resource optimization

## Shared Responsibilities
1. Documentation
   - Each team member documents their component
   - API documentation for their services
2. Testing
   - Unit tests for their components
   - Integration testing participation
3. Code Review
   - Cross-review of related components
   - Performance review of their domain

## Dependencies
1. Database Admin -> ML Engineer
   - Database schema needed for RAG implementation
2. DevOps Engineers -> All
   - Infrastructure needed for all deployments
3. ML Engineer -> DevOps
   - Resource requirements for ML components

## Communication Channels
1. Daily Updates
   - Short status updates
   - Blocking issues
2. Weekly Sync
   - Progress review
   - Architecture discussions
3. Documentation
   - Shared documentation repository
   - API specifications