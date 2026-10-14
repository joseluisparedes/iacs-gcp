terraform {
  required_version = ">= 1.9.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ------------------------------------------------------------------------------
# 1. Habilitación de APIs de Google Cloud
# ------------------------------------------------------------------------------
resource "google_project_service" "enabled_services" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "compute.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

# ------------------------------------------------------------------------------
# 2. Cloud SQL for PostgreSQL 17.x
# ------------------------------------------------------------------------------
resource "google_sql_database_instance" "postgres" {
  name             = "iacs-${var.environment}-db"
  database_version = "POSTGRES_17"
  region           = var.region

  settings {
    tier = var.db_tier
    backup_configuration {
      enabled    = true
      start_time = "04:00"
    }
    ip_configuration {
      ipv4_enabled = true
      ssl_mode     = "ENCRYPTED_ONLY"
    }
    insights_config {
      query_insights_enabled  = true
      record_application_tags = true
    }
  }

  deletion_protection = var.db_deletion_protection
  depends_on          = [google_project_service.enabled_services]
}

resource "google_sql_database" "database" {
  name     = "iacs_db"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "db_user" {
  name     = "iacs_user"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# ------------------------------------------------------------------------------
# 3. Google Cloud Run — Servicio Backend (FastAPI / Python 3.13)
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "backend" {
  name     = "iacs-${var.environment}-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend_sa.email

    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = 10
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres.connection_name]
      }
    }

    containers {
      image = var.backend_image

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      ports {
        container_port = 8000
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      # Variables de Entorno Generales
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "DEBUG"
        value = var.environment == "prod" ? "false" : "true"
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_LOCATION"
        value = var.region
      }
      env {
        name  = "VERTEX_AI_MODEL"
        value = var.vertex_ai_model
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.documents.name
      }
      env {
        name  = "USE_AUTH_MOCK"
        value = "false"
      }
      env {
        name  = "USE_AI_MOCK"
        value = "false"
      }
      env {
        name  = "USE_STORAGE_MOCK"
        value = "false"
      }
      env {
        name  = "USE_EMAIL_MOCK"
        value = var.use_email_mock ? "true" : "false"
      }

      # Cadena de Conexión a Cloud SQL vía Socket Unix de Cloud Run
      env {
        name  = "DATABASE_URL"
        value = "postgresql+asyncpg://iacs_user:${random_password.db_password.result}@/iacs_db?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
      }

      # Inyección de Secretos desde Secret Manager
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt_secret.secret_id
            version = "latest"
          }
        }
      }

      # Health Probes
      startup_probe {
        http_get {
          path = "/api/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 5
      }

      liveness_probe {
        http_get {
          path = "/api/health"
          port = 8000
        }
        period_seconds    = 15
        failure_threshold = 3
      }
    }
  }

  depends_on = [
    google_sql_database.database,
    google_sql_user.db_user,
    google_project_service.enabled_services
  ]
}

# ------------------------------------------------------------------------------
# 4. Google Cloud Run — Servicio Frontend (Nuxt 4 / Vue 3 SPA)
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "frontend" {
  name     = "iacs-${var.environment}-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.frontend_sa.email

    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = 10
    }

    containers {
      image = var.frontend_image

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      ports {
        container_port = 3000
      }

      env {
        name  = "NODE_ENV"
        value = "production"
      }
      env {
        name  = "NUXT_PUBLIC_API_BASE"
        value = "${google_cloud_run_v2_service.backend.uri}/api/v1"
      }
      env {
        name  = "NUXT_PUBLIC_APP_NAME"
        value = "IACS Enterprise"
      }
    }
  }

  depends_on = [
    google_cloud_run_v2_service.backend,
    google_project_service.enabled_services
  ]
}
