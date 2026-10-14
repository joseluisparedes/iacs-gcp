output "backend_url" {
  description = "URL pública del backend en Cloud Run"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "URL pública del frontend en Cloud Run"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "database_connection_name" {
  description = "Nombre de conexión de Cloud SQL para Cloud Run"
  value       = google_sql_database_instance.postgres.connection_name
}

output "storage_bucket_name" {
  description = "Nombre del bucket de Google Cloud Storage para documentos"
  value       = google_storage_bucket.documents.name
}

output "artifact_registry_repo" {
  description = "Identificador del repositorio de Artifact Registry para imágenes Docker"
  value       = google_artifact_registry_repository.iacs_repo.name
}

output "backend_service_account" {
  description = "Email de la cuenta de servicio del backend de Cloud Run"
  value       = google_service_account.backend_sa.email
}

output "frontend_service_account" {
  description = "Email de la cuenta de servicio del frontend de Cloud Run"
  value       = google_service_account.frontend_sa.email
}
