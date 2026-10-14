import logging
from typing import List, Optional
import httpx
from app.core.config import settings
from app.integrations.email.base import BaseEmailService

logger = logging.getLogger(__name__)


class Microsoft365EmailService(BaseEmailService):
    """
    Proveedor para Microsoft 365 / Exchange Online mediante Microsoft Graph API
    con modo de simulación y bitácora para desarrollo local.
    """

    def __init__(self):
        self.use_mock = settings.USE_EMAIL_MOCK
        self.tenant_id = settings.M365_TENANT_ID
        self.client_id = settings.M365_CLIENT_ID
        self.client_secret = settings.M365_CLIENT_SECRET
        self.sender = settings.EMAIL_SENDER

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        cc: Optional[List[str]] = None,
        initiative_id: Optional[str] = None,
    ) -> bool:
        logger.info(f"[Email Service] Destinatario: {to_email} | Asunto: '{subject}' | Iniciativa: {initiative_id}")

        if self.use_mock or not (self.tenant_id and self.client_id and self.client_secret):
            logger.info(f"[Email Simulator] Correo simulado y registrado exitosamente para {to_email}")
            return True

        # Implementación con Microsoft Graph API (OAuth2 Client Credentials Flow)
        try:
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": "https://graph.microsoft.com/.default",
                    },
                )
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    logger.error(f"[Email Error] No se pudo obtener token de M365: {token_data}")
                    return False

                # Enviar correo vía Graph API
                send_mail_url = f"https://graph.microsoft.com/v1.0/users/{self.sender}/sendMail"
                email_payload = {
                    "message": {
                        "subject": subject,
                        "body": {"contentType": "HTML", "content": html_content},
                        "toRecipients": [{"emailAddress": {"address": to_email}}],
                    },
                    "saveToSentItems": "true",
                }
                if cc:
                    email_payload["message"]["ccRecipients"] = [
                        {"emailAddress": {"address": addr}} for addr in cc
                    ]

                resp = await client.post(
                    send_mail_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json=email_payload,
                )
                if resp.status_code in (200, 202):
                    logger.info(f"[Email M365] Correo enviado exitosamente a {to_email}")
                    return True
                else:
                    logger.error(f"[Email M365 Error] Respuesta {resp.status_code}: {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"[Email Exception] Error al enviar correo vía M365: {e}")
            return False
