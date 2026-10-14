# ------------------------------------------------------------------------------
# Google Artifact Registry — Repositorio OCI para Imágenes Docker
# ------------------------------------------------------------------------------

resource "google_artifact_registry_repository" "iacs_repo" {
  location      = var.region
  repository_id = "iacs-${var.environment}-repo"
  description   = "Repositorio Docker para imágenes de IACS Enterprise (${var.environment})"
  format        = "DOCKER"

  labels = {
    app         = "iacs"
    environment = var.environment
  }
}
