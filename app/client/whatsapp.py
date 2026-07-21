import logging
from typing import Dict, Any, List, Optional
import httpx
from app.config import settings

logger = logging.getLogger("whatsapp_client")


class WhatsAppClient:
    """
    Async HTTPX Client for Meta WhatsApp Cloud API endpoint.
    Endpoint: https://graph.facebook.com/{META_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages
    """

    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = settings.META_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal helper to execute HTTP POST to Meta Graph API with retry on connection timeout."""
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.base_url,
                        json=payload,
                        headers=self.headers,
                    )
                    response_json = response.json()
                    if response.status_code >= 400:
                        logger.error(f"WhatsApp API Error [{response.status_code}]: {response_json}")
                    else:
                        logger.info(f"WhatsApp API Success [{response.status_code}]: {response_json}")
                    return response_json
            except httpx.HTTPError as exc:
                logger.warning(f"HTTP POST attempt {attempt + 1} failed: {exc}")
                if attempt == 1:
                    logger.error(f"WhatsApp API request failed after 2 attempts: {exc}")
                    return {"error": str(exc)}
        return {"error": "Failed after max retries"}

    async def send_text_message(
        self,
        to: str,
        text: str,
        reply_to_wamid: Optional[str] = None,
        preview_url: bool = False,
    ) -> Dict[str, Any]:
        """Send a standard plain text message to a WhatsApp user."""
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text,
            },
        }
        if reply_to_wamid:
            payload["context"] = {"message_id": reply_to_wamid}

        return await self._post(payload)

    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive message with up to 3 quick reply buttons.
        `buttons` format: [{"id": "btn_pricing", "title": "View Pricing"}, ...]
        """
        action_buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": btn.get("id"),
                    "title": btn.get("title")[:20],  # Meta max 20 chars for button title
                },
            }
            for btn in buttons[:3]
        ]

        # Truncate body_text to 1000 characters to comply with Meta's 1024 char limit
        safe_body_text = body_text[:1000] if body_text else "Select an option below:"

        interactive: Dict[str, Any] = {
            "type": "button",
            "body": {"text": safe_body_text},
            "action": {"buttons": action_buttons},
        }

        if header_text:
            interactive["header"] = {"type": "text", "text": header_text[:60]}
        if footer_text:
            interactive["footer"] = {"text": footer_text[:60]}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        return await self._post(payload)

    async def send_interactive_list(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive list message with multiple sections and options.
        `sections` format: [{"title": "Section Title", "rows": [{"id": "r1", "title": "Row Title", "description": "..."}]}]
        """
        safe_body_text = body_text[:1000] if body_text else "Select an option from the menu below:"

        interactive: Dict[str, Any] = {
            "type": "list",
            "body": {"text": safe_body_text},
            "action": {
                "button": button_text[:20],
                "sections": sections,
            },
        }

        if header_text:
            interactive["header"] = {"type": "text", "text": header_text[:60]}
        if footer_text:
            interactive["footer"] = {"text": footer_text[:60]}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        return await self._post(payload)

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send a WhatsApp message template."""
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
        if components:
            payload["template"]["components"] = components

        return await self._post(payload)

    async def download_media(self, media_id: str) -> Optional[bytes]:
        """Downloads raw media file bytes from Meta Cloud API by media_id."""
        try:
            url = f"https://graph.facebook.com/{self.api_version}/{media_id}"
            headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    media_url = res.json().get("url")
                    if media_url:
                        media_res = await client.get(media_url, headers=headers)
                        if media_res.status_code == 200:
                            return media_res.content
        except Exception as exc:
            logger.error(f"Error downloading media {media_id}: {exc}")
        return None


whatsapp_client = WhatsAppClient()
