import logging
import httpx
from app.config import settings

logger = logging.getLogger("telnyx_client")

class TelnyxClient:
    """
    Async client for the Telnyx Call Control API (v2).
    """
    def __init__(self):
        self.api_key = settings.TELNYX_API_KEY
        self.base_url = "https://api.telnyx.com/v2/calls"

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _post(self, path: str, payload: dict = None) -> dict:
        """Internal helper to execute POST request to Telnyx API."""
        url = f"{self.base_url}/{path}" if path else self.base_url
        if not self.api_key:
            logger.error("TELNYX_API_KEY is not configured in settings.")
            return {"error": "Missing Telnyx API Key"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info(f"Telnyx API Request: POST {url} with payload {payload}")
                response = await client.post(url, json=payload, headers=self.headers)
                response_json = response.json()
                if response.status_code >= 400:
                    logger.error(f"Telnyx API Error [{response.status_code}]: {response_json}")
                else:
                    logger.info(f"Telnyx API Success [{response.status_code}]")
                return response_json
        except Exception as exc:
            logger.error(f"Telnyx API Request failed: {exc}", exc_info=True)
            return {"error": str(exc)}

    async def dial_outbound_call(
        self,
        to_number: str,
        from_number: str = None,
        client_state: str = None,
    ) -> dict:
        """
        Initiates an outbound call via Telnyx Call Control API (v2).
        POST https://api.telnyx.com/v2/calls
        """
        from_num = from_number or settings.TELNYX_PHONE_NUMBER or "+19255040101"
        domain = settings.SERVER_DOMAIN or "api.engine.astraventa.com"
        webhook_url = f"https://{domain}/webhook/voice"

        payload = {
            "to": to_number,
            "from": from_num,
            "connection_id": settings.TELNYX_CONNECTION_ID or "3011985982435100116",
            "webhook_url": webhook_url,
        }
        if client_state:
            payload["client_state"] = client_state

        logger.info(f"Initiating outbound Telnyx call: from={from_num} to={to_number} connection={payload['connection_id']}")
        return await self._post("", payload)

    async def answer_call(self, call_control_id: str) -> dict:
        """Answer an incoming call."""
        # We can specify status_callback if needed, otherwise it defaults to the App settings
        payload = {}
        return await self._post(f"{call_control_id}/actions/answer", payload)

    async def start_media_stream(self, call_control_id: str, stream_url: str) -> dict:
        """
        Starts bi-directional raw media streaming (RTP over WebSockets) for the call.
        """
        payload = {
            "stream_url": stream_url,
            "stream_track": "inbound_track",
            "stream_bidirectional_mode": "rtp",
            "stream_bidirectional_codec": "PCMU"
        }
        return await self._post(f"{call_control_id}/actions/streaming_start", payload)

    async def transfer_call(self, call_control_id: str, target: str) -> dict:
        """
        Transfers the active call to a SIP URI or phone number.
        target example: 'sip:userzeeshan35793@sip.telnyx.com' or '+923055255838'
        """
        payload = {
            "to": target
        }
        logger.info(f"Transferring call {call_control_id} to {target}")
        return await self._post(f"{call_control_id}/actions/transfer", payload)

    async def hangup_call(self, call_control_id: str) -> dict:
        """Hangs up the call."""
        return await self._post(f"{call_control_id}/actions/hangup")

    async def send_sms(self, from_number: str, to_number: str, text: str) -> dict:
        """
        Sends an SMS message using the Telnyx Messaging API (v2).
        """
        url = "https://api.telnyx.com/v2/messages"
        payload = {
            "from": from_number,
            "to": to_number,
            "text": text
        }
        if not self.api_key:
            logger.error("TELNYX_API_KEY is not configured in settings.")
            return {"error": "Missing Telnyx API Key"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info(f"Telnyx SMS Request: POST {url} from {from_number} to {to_number}")
                response = await client.post(url, json=payload, headers=self.headers)
                response_json = response.json()
                if response.status_code >= 400:
                    logger.error(f"Telnyx SMS Error [{response.status_code}]: {response_json}")
                else:
                    logger.info(f"Telnyx SMS Success [{response.status_code}]")
                return response_json
        except Exception as exc:
            logger.error(f"Telnyx SMS Request failed: {exc}", exc_info=True)
            return {"error": str(exc)}

telnyx_client = TelnyxClient()
