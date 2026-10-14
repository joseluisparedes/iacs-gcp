from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAIService(ABC):
    """
    Contrato abstracto para el servicio de Inteligencia Artificial (Vertex AI).
    Asegura que la lógica de negocio no dependa de implementaciones concretas.
    """

    @abstractmethod
    async def chat(
        self,
        system_prompt: str,
        history: List[Dict[str, Any]],
        message: str,
        temperature: float = 0.2,
        initial_data: Optional[Dict[str, Any]] = None,
        ai_fields: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Genera una respuesta conversacional estructurada para el chat con Teo."""
        pass

    @abstractmethod
    async def summarize(
        self,
        system_prompt: str,
        history: List[Dict[str, Any]],
        initial_data: Dict[str, Any],
        fields_schema: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Sintetiza la conversación y extrae los campos de la iniciativa en formato estructurado."""
        pass

    @abstractmethod
    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/webm",
        domain_prompt: Optional[str] = None,
    ) -> str:
        """Transcribe audio a texto en español utilizando capacidades multimodales."""
        pass

    @abstractmethod
    async def extract_document_text(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
    ) -> str:
        """Extrae el contenido textual de documentos (PDF, DOCX, XLSX, TXT)."""
        pass
