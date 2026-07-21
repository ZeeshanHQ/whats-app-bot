import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any

from app.config import settings
from app.routers import webhook_router, ai_test_router
from app.client.whatsapp import whatsapp_client

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")

app = FastAPI(
    title="Meta WhatsApp Cloud API Bot",
    description="FastAPI server for handling Meta WhatsApp Webhooks and Gemini AI automated responses.",
    version="2.0.0",
)

# Enable CORS for Next.js dashboard calls from localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(webhook_router)
app.include_router(ai_test_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "WhatsApp Cloud API Gemini AI Server",
        "meta_api_version": settings.META_API_VERSION,
        "phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID,
        "ai_model": settings.GEMINI_MODEL,
    }


class TemplateSendRequest(BaseModel):
    to: str
    template_name: str = "jaspers_market_order_confirmation_v1"
    language_code: str = "en_US"
    components: Optional[List[Any]] = None


@app.post("/api/send-template", tags=["Outbound"])
async def send_template_endpoint(req: TemplateSendRequest):
    """
    Outbound client helper endpoint to send template messages.
    """
    try:
        response = await whatsapp_client.send_template_message(
            to=req.to,
            template_name=req.template_name,
            language_code=req.language_code,
            components=req.components,
        )
        return response
    except Exception as exc:
        logger.error(f"Failed to send template message: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


class TextSendRequest(BaseModel):
    to: str
    text: str


@app.post("/api/send-text", tags=["Outbound"])
async def send_text_endpoint(req: TextSendRequest):
    """
    Outbound client helper endpoint to send plain text messages.
    """
    try:
        response = await whatsapp_client.send_text_message(
            to=req.to,
            text=req.text,
        )
        return response
    except Exception as exc:
        logger.error(f"Failed to send text message: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
