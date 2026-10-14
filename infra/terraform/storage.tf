# ------------------------------------------------------------------------------
# Google Cloud Storage (GCS) — Almacenamiento de Documentos y Evidencias
# ------------------------------------------------------------------------------

resource "google_storage_bucket" "documents" {
  name                        = "${var.project_id}-${var.environment}-documents"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  cors {
    origin          = ["http://localhost:3000", "https://*.run.app"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    condition {
      age = 365 # Retención de versiones antiguas por 1 año
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    app         = "iacs"
    environment = var.environment
  }
}

# Permisos de la cuenta de servicio de backend sobre el bucket
resource "google_storage_bucket_iam_member" "backend_storage_admin" {
  bucket = google_storage_bucket.documents.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend_sa.email}"
}
