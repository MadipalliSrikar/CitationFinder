# infrastructure/terraform/main.tf

terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
  spaces_access_id  = var.spaces_access_id
  spaces_secret_key = var.spaces_secret_key
}

# DOKS Cluster
resource "digitalocean_kubernetes_cluster" "citation_finder" {
  name    = "citation-finder-cluster"
  region  = "sfo3"
  version = "1.29.9-do.4"    # Updated to valid version

  node_pool {
    name       = "worker-pool"
    size       = "s-2vcpu-4gb"
    node_count = 2
  }
}

# PostgreSQL Database
resource "digitalocean_database_cluster" "postgres" {
  name       = "citation-finder-db"
  engine     = "pg"
  version    = "15"
  size       = "db-s-1vcpu-1gb"
  region     = "sfo3"
  node_count = 1
}

# Spaces Bucket for Document Storage
resource "digitalocean_spaces_bucket" "document_storage" {
  name   = "citation-finder-documents"
  region = "sfo3"
  acl    = "private"
}