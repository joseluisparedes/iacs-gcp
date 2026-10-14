from abc import ABC, abstractmethod
from typing import Optional


class BaseStorageService(ABC):
    """
    Interfaz abstracta para el almacenamiento de archivos (Google Cloud Storage)
    según la regla §10 de Instructivo.md.
    """

    @abstractmethod
    async def upload_file(
        self,
        file_bytes: bytes,
        destination_path: str,
        content_type: str = "application/octet-stream",
        bucket_name: Optional[str] = None,
    ) -> str:
        """Sube un archivo y retorna su URL pública o identificador persistente."""
        pass

    @abstractmethod
    async def download_file(
        self,
        file_path: str,
        bucket_name: Optional[str] = None,
    ) -> bytes:
        """Descarga el contenido binario de un archivo."""
        pass

    @abstractmethod
    async def delete_file(
        self,
        file_path: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Elimina un archivo del almacenamiento."""
        pass
