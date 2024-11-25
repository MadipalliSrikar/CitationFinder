# infrastructure/terraform/variables.tf

variable "do_token" {
  description = "DigitalOcean API Token"
  type        = string
  sensitive   = true
}

variable "spaces_access_id" {
  description = "DigitalOcean Spaces Access ID"
  type        = string
  sensitive   = true
}

variable "spaces_secret_key" {
  description = "DigitalOcean Spaces Secret Key"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "citation-finder"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "development"
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "sfo3"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.29.9-do.4"
}

variable "node_pool_size" {
  description = "Size of node pool VMs"
  type        = string
  default     = "s-2vcpu-4gb"
}

variable "node_pool_count" {
  description = "Number of nodes in the pool"
  type        = number
  default     = 2
}

variable "db_size" {
  description = "Database size"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "db_node_count" {
  description = "Number of database nodes"
  type        = number
  default     = 1
}

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15"
}