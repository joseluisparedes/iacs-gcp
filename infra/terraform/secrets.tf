# ------------------------------------------------------------------------------
# Google Secret Manager — Gestión Centralizada de Secretos Corporativos
# ------------------------------------------------------------------------------

# 1. Secreto: Contraseña de la Base de Datos PostgreSQL 17
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "iacs-${var.environment}-db-password"
  replication {
    auto {}
  }
  labels = {
    app         = "iacs"
    environment = var.environment
  }
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret_iam_member" "backend_access_db_password" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

# 2. Secreto: Llave Criptográfica JWT para Sesión de Usuarios
resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "iacs-${var.environment}-jwt-secret"
  replication {
    auto {}
  }
  labels = {
    app         = "iacs"
    environment = var.environment
  }
}

resource "google_secret_manager_secret_version" "jwt_secret_version" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}

resource "google_secret_manager_secret_iam_member" "backend_access_jwt_secret" {
  secret_id = google_secret_manager_secret.jwt_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}
