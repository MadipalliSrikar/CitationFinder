terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

variable "do_token" {}

provider "digitalocean" {
  token = var.do_token
}

# DOKS Cluster
resource "digitalocean_kubernetes_cluster" "citation_finder" {
  name    = "citation-finder-cluster"
  region  = "nyc1"
  version = "1.28.2-do.0"

  node_pool {
    name       = "worker-pool"
    size       = "s-2vcpu-4gb"
    node_count = 2
  }
}

# PostgreSQL Database
resource "digitalocean_database_cluster" "postgres" {
  name                 = "citation-finder-db"
  engine              = "pg"
  version             = "15"
  size                = "db-s-1vcpu-1gb"
  region              = "nyc1"
  node_count          = 1
}

# Spaces Bucket for Document Storage
resource "digitalocean_spaces_bucket" "document_storage" {
  name   = "citation-finder-documents"
  region = "nyc3"
  acl    = "private"
}