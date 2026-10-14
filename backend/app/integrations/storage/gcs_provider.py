import logging
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.integrations.storage.base import BaseStorageService

logger = logging.getLogger(__name__)


class CloudStorageService(BaseStorageService):
    """
    Proveedor de almacenamiento para Google Cloud Storage (GCS)
    con fallback a sistema de archivos local para desarrollo.
    """

    def __init__(self):
        self.use_mock = settings.USE_STORAGE_MOCK
        self.local_path = Path(settings.LOCAL_STORAGE_PATH)
        self.default_bucket = settings.GCS_BUCKET_DOCUMENTS
        self._client = None

        if not self.use_mock:
            try:
                from google.cloud import storage
                self._client = storage.Client(project=settings.GCP_PROJECT_ID)
                logger.info("Google Cloud Storage inicializado con éxito.")
            except Exception as e:
                logger.warning(f"No se pudo conectar a GCS ({e}). Usando almacenamiento local.")
                self.use_mock = True

        if self.use_mock:
            self.local_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file_bytes: bytes,
        destination_path: str,
        content_type: str = "application/octet-stream",
        bucket_name: Optional[str] = None,
    ) -> str:
        if self.use_mock or not self._client:
            target_file = self.local_path / destination_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, "wb") as f:
                f.write(file_bytes)
            return f"/uploads/{destination_path}"

        try:
            target_bucket = self._client.bucket(bucket_name or self.default_bucket)
            blob = target_bucket.blob(destination_path)
            blob.upload_from_string(file_bytes, content_type=content_type)
            return blob.public_url or f"gs://{target_bucket.name}/{destination_path}"
        except Exception as err:
            logger.error(f"Error subiendo archivo a GCS: {err}")
            raise

    async def download_file(
        self,
        file_path: str,
        bucket_name: Optional[str] = None,
    ) -> bytes:
        if self.use_mock or not self._client:
            clean_path = file_path.removeprefix("/uploads/").removeprefix("uploads/").removeprefix("/")
            target_file = self.local_path / clean_path
            if not target_file.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            with open(target_file, "rb") as f:
                return f.read()

        try:
            target_bucket = self._client.bucket(bucket_name or self.default_bucket)
            blob = target_bucket.blob(file_path)
            return blob.download_as_bytes()
        except Exception as err:
            logger.error(f"Error descargando archivo de GCS: {err}")
            raise

    async def delete_file(
        self,
        file_path: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        if self.use_mock or not self._client:
            clean_path = file_path.removeprefix("/uploads/").removeprefix("uploads/").removeprefix("/")
            target_file = self.local_path / clean_path
            if target_file.exists():
                target_file.unlink()
                return True
            return False

        try:
            target_bucket = self._client.bucket(bucket_name or self.default_bucket)
            blob = target_bucket.blob(file_path)
            blob.delete()
            return True
        except Exception as err:
            logger.error(f"Error eliminando archivo de GCS: {err}")
            return False
