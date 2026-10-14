# ------------------------------------------------------------------------------
# Cuentas de Servicio (Service Accounts) e IAM con Principio de Mínimo Privilegio
# ------------------------------------------------------------------------------

# 1. Cuenta de Servicio dedicada para el Backend (FastAPI)
resource "google_service_account" "backend_sa" {
  account_id   = "iacs-${var.environment}-backend-sa"
  display_name = "IACS Backend Cloud Run Service Account (${var.environment})"
  description  = "Cuenta de servicio con permisos mínimos para el backend de IACS en Cloud Run"
}

# 2. Cuenta de Servicio dedicada para el Frontend (Nuxt 4)
resource "google_service_account" "frontend_sa" {
  account_id   = "iacs-${var.environment}-frontend-sa"
  display_name = "IACS Frontend Cloud Run Service Account (${var.environment})"
  description  = "Cuenta de servicio para el frontend de IACS en Cloud Run"
}

# 3. Permisos de Backend: Conexión a Cloud SQL (PostgreSQL 17)
resource "google_project_iam_member" "backend_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# 4. Permisos de Backend: Acceso a Vertex AI (Gemini 2.5 Flash / Pro)
resource "google_project_iam_member" "backend_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# 5. Permisos de Backend: Escritura de Logs en Cloud Logging
resource "google_project_iam_member" "backend_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# 6. Permisos de Backend: Métricas en Cloud Monitoring
resource "google_project_iam_member" "backend_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# 7. Permisos de Invocación Pública para Cloud Run (Configurable)
resource "google_cloud_run_v2_service_iam_member" "backend_invoker" {
  count    = var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_invoker" {
  count    = var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.frontend.name
  location = google_cloud_run_v2_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
