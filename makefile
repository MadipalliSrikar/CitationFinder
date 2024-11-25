# Makefile

.PHONY: init deploy test clean docker-build docker-push

# Infrastructure
init:
	cd infrastructure/terraform && terraform init

plan:
	cd infrastructure/terraform && terraform plan

apply:
	cd infrastructure/terraform && terraform apply

destroy:
	cd infrastructure/terraform && terraform destroy

# Docker
docker-build:
	docker-compose -f docker/docker-compose.yml build

docker-up:
	docker-compose -f docker/docker-compose.yml up -d

docker-down:
	docker-compose -f docker/docker-compose.yml down

# Development
install:
	pip install -r services/data-ingestion/requirements.txt
	pip install -r services/document-processor/requirements.txt
	pip install -r services/rag-service/requirements.txt
	pip install -r services/api-gateway/requirements.txt

test:
	pytest services/*/tests/

lint:
	flake8 services/

# Kubernetes
k8s-apply:
	kubectl apply -f infrastructure/k8s/base/
	kubectl apply -f infrastructure/k8s/overlays/dev/

k8s-delete:
	kubectl delete -f infrastructure/k8s/overlays/dev/
	kubectl delete -f infrastructure/k8s/base/

# Clean
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete