from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Entorno
    ENVIRONMENT: str = "local"
    DEBUG: bool = True
    APP_NAME: str = "IACS Enterprise (GCP)"

    # Base de Datos
    DATABASE_URL: str = "postgresql+asyncpg://iacs_user:iacs_secure_password_dev@postgres:5432/iacs_db"

    # Seguridad y JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars-long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    USE_AUTH_MOCK: bool = True

    # IdP Corporativo (SecureAuth)
    IDP_ISSUER_URL: str = "https://login.corporativo.com"
    IDP_CLIENT_ID: str = "iacs-app-client-id"
    IDP_AUDIENCE: str = "iacs-api"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Google Cloud & Vertex AI / LLM Engine Cascade
    GCP_PROJECT_ID: str = "iacs-enterprise-prod"
    GCP_LOCATION: str = "us-central1"
    VERTEX_AI_MODEL: str = "gemini-3.8-flash"
    USE_AI_MOCK: bool = False

    # AI Enterprise Providers
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Almacenamiento (Google Cloud Storage)
    USE_STORAGE_MOCK: bool = True
    GCS_BUCKET_DOCUMENTS: str = "iacs-documents-storage"
    GCS_BUCKET_AVATARS: str = "iacs-avatars-storage"
    LOCAL_STORAGE_PATH: str = "/app/uploads"

    # Correo (Microsoft 365)
    USE_EMAIL_MOCK: bool = True
    M365_TENANT_ID: str = ""
    M365_CLIENT_ID: str = ""
    M365_CLIENT_SECRET: str = ""
    EMAIL_SENDER: str = "no-reply@iacs.empresa.com"


settings = Settings()
