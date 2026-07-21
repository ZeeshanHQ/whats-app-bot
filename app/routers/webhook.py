import logging
from fastapi import APIRouter, Query, Response, HTTPException, status, BackgroundTasks, Request
from app.config import settings
from app.models.webhook import WebhookPayload
from app.services.message_handler import process_webhook_payload

logger = logging.getLogger("webhook_router")
router = APIRouter(tags=["Webhook"])


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    1. GET /webhook
    Verifies Meta WhatsApp Webhook endpoint subscription.
    Returns hub.challenge in plain text with 200 OK if hub.verify_token matches.
    """
    logger.info(f"Verification request received: mode={hub_mode}, token={hub_verify_token}")

    if hub_mode == "subscribe" and hub_verify_token == settings.WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook subscription verified successfully.")
        return Response(content=hub_challenge, media_type="text/plain", status_code=200)

    logger.warning("Webhook verification failed: Invalid token or mode.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification failed. Invalid mode or verify_token.",
    )


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    2. POST /webhook
    Instantly returns 200 OK to Meta servers.
    Parses and processes incoming user messages asynchronously in the background.
    """
    try:
        raw_bytes = await request.body()
        raw_str = raw_bytes.decode("utf-8", errors="ignore")
        logger.info(f"Received Webhook POST payload: {raw_str}")

        raw_json = await request.json()
        payload = WebhookPayload.model_validate(raw_json)

        # Dispatch background task to process payload asynchronously
        background_tasks.add_task(process_webhook_payload, payload)

    except Exception as exc:
        logger.error(f"Error parsing webhook payload: {exc}", exc_info=True)

    # Always return 200 OK to Meta instantly
    return {"status": "ok"}
