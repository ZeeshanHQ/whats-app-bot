import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.ai_brain import ai_service
from app.services.memory import memory_manager
from app.client.whatsapp import whatsapp_client

logger = logging.getLogger("ai_test_router")
router = APIRouter(prefix="/api", tags=["AI Engine & Testing"])


class AIChatRequest(BaseModel):
    wa_id: str = "test_user"
    message: str


class AIChatResponse(BaseModel):
    wa_id: str
    message: str
    ai_reply: str
    history: List[Dict[str, str]]


class EmbedRequest(BaseModel):
    text: str


class InteractiveTestRequest(BaseModel):
    to: str = "923055255838"
    type: str = "button"  # "button" or "list"
    body_text: Optional[str] = "Welcome to Astraventa! How can we help you today?"


@router.post("/ai/chat", response_model=AIChatResponse)
async def ai_chat_endpoint(req: AIChatRequest):
    """
    Local testing endpoint to test Gemini AI Engine output & memory state.
    """
    try:
        ai_reply = await ai_service.process_user_query(
            wa_id=req.wa_id,
            prompt=req.message,
        )
        current_history = await memory_manager.get_history_async(req.wa_id)

        return AIChatResponse(
            wa_id=req.wa_id,
            message=req.message,
            ai_reply=ai_reply,
            history=current_history,
        )
    except Exception as exc:
        logger.error(f"Error in /api/ai/chat endpoint: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/ai/embed")
async def ai_embed_endpoint(req: EmbedRequest):
    """
    Generates 768-dimensional vector embedding for knowledge base insertion.
    """
    try:
        embedding = await ai_service.generate_embedding(req.text)
        if not embedding:
            embedding = [0.01] * 768
        return {"embedding": embedding}
    except Exception as exc:
        logger.error(f"Error in /api/ai/embed endpoint: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/ai/memory/{wa_id}")
async def get_memory_endpoint(wa_id: str):
    """
    Retrieves current conversation history for specified wa_id.
    """
    history = await memory_manager.get_history_async(wa_id)
    return {
        "wa_id": wa_id,
        "turns": len(history) // 2,
        "history": history,
    }


@router.delete("/ai/memory/{wa_id}")
async def clear_memory_endpoint(wa_id: str):
    """
    Clears session memory history for wa_id.
    """
    await memory_manager.clear_history_async(wa_id)
    return {
        "status": "cleared",
        "wa_id": wa_id,
    }


@router.post("/test/interactive")
async def test_interactive_endpoint(req: InteractiveTestRequest):
    """
    Local test endpoint to send outbound Interactive Buttons or List payloads.
    """
    try:
        if req.type == "list":
            sections = [
                {
                    "title": "Astraventa Packages",
                    "rows": [
                        {"id": "btn_pricing", "title": "Starter & Enterprise", "description": "$499/mo & $1,499/mo"},
                        {"id": "btn_services", "title": "AI & Automation", "description": "WhatsApp & AI Agents"},
                    ]
                },
                {
                    "title": "Contact & Booking",
                    "rows": [
                        {"id": "btn_book_call", "title": "Book Consultation", "description": "Schedule a 15-min call"},
                    ]
                }
            ]
            response = await whatsapp_client.send_interactive_list(
                to=req.to,
                body_text=req.body_text or "Choose an option from the menu below:",
                button_text="View Options",
                sections=sections,
                header_text="Astraventa Services",
                footer_text="Powered by Gemini AI",
            )
        else:
            # Default interactive quick reply buttons
            buttons = [
                {"id": "btn_pricing", "title": "View Pricing"},
                {"id": "btn_services", "title": "View Services"},
                {"id": "btn_book_call", "title": "Book a Call"},
            ]
            response = await whatsapp_client.send_interactive_buttons(
                to=req.to,
                body_text=req.body_text or "How would you like to proceed?",
                buttons=buttons,
                header_text="Astraventa Menu",
                footer_text="Select an option below",
            )
        return response
    except Exception as exc:
        logger.error(f"Error in /api/test/interactive endpoint: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
