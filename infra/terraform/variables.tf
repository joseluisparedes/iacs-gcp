variable "project_id" {
  description = "ID del proyecto en Google Cloud Platform"
  type        = string
  default     = "iacs-enterprise-prod"
}

variable "region" {
  description = "Región principal de GCP para despliegue de recursos"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Entorno de despliegue (dev, qa, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "qa", "prod"], var.environment)
    error_message = "El entorno debe ser uno de: dev, qa, prod."
  }
}

variable "backend_image" {
  description = "URI de la imagen de contenedor del backend en Artifact Registry"
  type        = string
  default     = "us-central1-docker.pkg.dev/iacs-enterprise-prod/iacs-prod-repo/backend:latest"
}

variable "frontend_image" {
  description = "URI de la imagen de contenedor del frontend en Artifact Registry"
  type        = string
  default     = "us-central1-docker.pkg.dev/iacs-enterprise-prod/iacs-prod-repo/frontend:latest"
}

variable "db_tier" {
  description = "Tipo de máquina para Cloud SQL PostgreSQL 17 (e.g. db-custom-2-7680, db-f1-micro)"
  type        = string
  default     = "db-custom-2-7680"
}

variable "db_deletion_protection" {
  description = "Activar protección contra borrado accidental de la base de datos"
  type        = bool
  default     = true
}

variable "vertex_ai_model" {
  description = "Modelo de Vertex AI a utilizar por el backend para Teo"
  type        = string
  default     = "gemini-2.5-flash"
}

variable "allow_unauthenticated" {
  description = "Permitir invocación pública unauthenticated a Cloud Run"
  type        = bool
  default     = true
}

variable "use_email_mock" {
  description = "Usar mock local de envío de correo en vez de Microsoft 365"
  type        = bool
  default     = false
}
