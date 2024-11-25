# infrastructure/terraform/outputs.tf

output "kubernetes_cluster_name" {
  value = digitalocean_kubernetes_cluster.citation_finder.name
}

output "kubernetes_endpoint" {
  value     = digitalocean_kubernetes_cluster.citation_finder.endpoint
  sensitive = true
}

output "database_endpoint" {
  value     = digitalocean_database_cluster.postgres.host
  sensitive = true
}

output "database_name" {
  value = digitalocean_database_cluster.postgres.database
}

output "spaces_bucket_name" {
  value = digitalocean_spaces_bucket.document_storage.name
}

output "spaces_endpoint" {
  value = digitalocean_spaces_bucket.document_storage.endpoint
}