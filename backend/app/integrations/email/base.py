from abc import ABC, abstractmethod
from typing import List, Optional


class BaseEmailService(ABC):
    """
    Interfaz abstracta para el servicio de correo (Microsoft 365 / Exchange Online)
    según la regla §13 de Instructivo.md.
    """

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        cc: Optional[List[str]] = None,
        initiative_id: Optional[str] = None,
    ) -> bool:
        """Envía un correo electrónico transaccional y registra su bitácora."""
        pass
