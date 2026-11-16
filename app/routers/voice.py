import json
import base64
import asyncio
import logging
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from app.config import settings
from app.client.telnyx import telnyx_client
from app.services.stt import DeepgramLiveClient
from app.services.tts import text_to_speech_pcmu
from app.services.ai_brain import ai_service
from app.services.db import (
    create_call_session,
    append_call_transcript,
    end_call_session,
)

logger = logging.getLogger("voice_router")
router = APIRouter(tags=["Voice Webhook & Outbound Calls"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class OutboundCallRequest(BaseModel):
    to_number: str
    campaign_name: Optional[str] = "Direct Outbound"
    custom_prompt: Optional[str] = None


# ---------------------------------------------------------------------------
# Outbound Call API Trigger
# ---------------------------------------------------------------------------

@router.post("/api/calls/outbound")
async def trigger_outbound_call(req: OutboundCallRequest):
    """
    Initiates an outbound AI voice call to a target phone number using Telnyx Call Control v2.
    When the recipient answers, the media stream connects to our AI Voice Engine
    and Sophia opens with the outbound pitch / prompt.
    """
    to_number = req.to_number.strip().replace(" ", "").replace("-", "")
    if not to_number.startswith("+"):
        to_number = f"+{to_number}"

    if len(to_number) < 8:
        raise HTTPException(status_code=400, detail="Invalid phone number format.")

    client_state_dict = {
        "direction": "outgoing",
        "campaign": req.campaign_name or "Direct Outbound",
        "custom_prompt": req.custom_prompt or "",
        "to_number": to_number,
    }
    encoded_state = base64.b64encode(json.dumps(client_state_dict).encode("utf-8")).decode("utf-8")

    logger.info(f"Triggering outbound AI call to: {to_number} (Campaign: {req.campaign_name})")

    res = await telnyx_client.dial_outbound_call(
        to_number=to_number,
        from_number=settings.TELNYX_PHONE_NUMBER or "+19255040101",
        client_state=encoded_state,
    )

    data = res.get("data", {})
    call_control_id = data.get("call_control_id")
    call_session_id = data.get("call_session_id")

    if not call_control_id:
        error_msg = res.get("errors") or res.get("error") or "Failed to initiate call via Telnyx."
        logger.error(f"Telnyx outbound dial failed: {error_msg}")
        raise HTTPException(status_code=400, detail=str(error_msg))

    # Pre-record the outbound session in Supabase demo_sessions
    db_session_id = None
    try:
        db_session_id = await create_call_session(
            call_control_id=call_control_id,
            from_number=to_number,
            session_type="outbound_phone",
        )
    except Exception as e:
        logger.warning(f"Could not pre-record outbound session: {e}")

    return {
        "success": True,
        "call_control_id": call_control_id,
        "call_session_id": call_session_id,
        "db_session_id": db_session_id,
        "to": to_number,
        "from": settings.TELNYX_PHONE_NUMBER or "+19255040101",
        "status": "dialing",
        "campaign": req.campaign_name,
    }


# ---------------------------------------------------------------------------
# Telnyx Call Control Webhook Handler
# ---------------------------------------------------------------------------

@router.post("/webhook/voice")
async def receive_voice_webhook(request: Request):
    """
    Handles Telnyx Call Control Webhook events for BOTH Inbound and Outbound calls.
    Routes:
      - call.initiated -> Answer incoming call (or log outgoing leg)
      - call.answered  -> Start bidirectional media streaming over WebSocket
      - call.hangup    -> Record completion and hangup cause
    """
    try:
        body = await request.body()
        if not body:
            return {"status": "empty_body"}

        payload = json.loads(body.decode("utf-8"))
        data = payload.get("data", {})
        event_type = data.get("event_type")
        event_payload = data.get("payload", {})
        call_control_id = event_payload.get("call_control_id")
        from_number = event_payload.get("from")
        to_number = event_payload.get("to")
        direction = event_payload.get("direction", "incoming")
        client_state = event_payload.get("client_state") or ""

        logger.info(f"Telnyx event: '{event_type}' (direction: {direction}) for call_control_id: {call_control_id}")

        if event_type == "call.initiated":
            if direction == "incoming":
                logger.info(f"Incoming call initiated from {from_number} to {to_number}. Answering...")
                await telnyx_client.answer_call(call_control_id)
            else:
                logger.info(f"Outbound call leg initiated to {to_number} (call_control_id: {call_control_id}).")

        elif event_type == "call.answered":
            logger.info(f"Call {call_control_id} answered (direction: {direction}). Starting media stream...")
            domain = settings.SERVER_DOMAIN or "api.engine.astraventa.com"
            stream_url = (
                f"wss://{domain}/webhook/voice/stream?"
                f"from_number={from_number}&to_number={to_number}&"
                f"direction={direction}&call_control_id={call_control_id}"
            )
            if client_state:
                stream_url += f"&client_state={client_state}"

            await telnyx_client.start_media_stream(call_control_id, stream_url)

        elif event_type == "call.hangup":
            hangup_cause = event_payload.get("hangup_cause", "unknown")
            sip_status = event_payload.get("sip_status", "unknown")
            logger.info(f"Call {call_control_id} hung up. Cause: {hangup_cause}, SIP Status: {sip_status}")

    except Exception as exc:
        logger.error(f"Error handling Telnyx webhook: {exc}", exc_info=True)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Bi-directional Audio Streaming WebSocket (Inbound + Outbound)
# ---------------------------------------------------------------------------

@router.websocket("/webhook/voice/stream")
async def voice_websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint handling raw bi-directional audio stream (PCMU over WebSocket).
    Features:
      - Fixed Speech-Loop: Declared nonlocal variables, eliminating UnboundLocalError
      - Robust turn-taking with Deepgram Live STT and sub-second Groq LPU response
      - Dual Mode: Supports both Inbound Greetings and Outbound Sales/Follow-up Pitches
      - Instant Caller Barge-In with Telnyx Media Buffer Clearing
      - Fast-Path Greeting Acknowledgment (~250ms dynamic reply to 'Hello?')
      - Real-time Session & Transcript Logging into Supabase demo_sessions
    """
    await websocket.accept()
    logger.info("Telnyx media WebSocket connection accepted.")

    # Extract call metadata from query parameters
    from_number = websocket.query_params.get("from_number", "anonymous").strip()
    to_number = websocket.query_params.get("to_number", "").strip()
    direction = websocket.query_params.get("direction", "incoming").strip().lower()
    call_control_id = websocket.query_params.get("call_control_id")
    client_state_raw = websocket.query_params.get("client_state", "")

    # For outbound, customer is to_number; for inbound, customer is from_number
    target_phone = to_number if direction in ("outgoing", "outbound") else from_number

    # Parse client_state if present for custom outbound prompt
    custom_outbound_prompt = None
    if client_state_raw:
        try:
            state_data = json.loads(base64.b64decode(client_state_raw).decode("utf-8"))
            custom_outbound_prompt = state_data.get("custom_prompt")
        except Exception:
            pass

    logger.info(f"Stream parameters: target={target_phone}, direction={direction}, call_control_id={call_control_id}")

    deepgram_client = None
    stream_id = None
    playback_task = None
    call_start_time = time.time()
    session_id = None
    is_speaking = False
    is_processing = False
    call_history = []
    fast_greet_count = 0

    session_type = "outbound_phone" if direction in ("outgoing", "outbound") else "inbound_phone"

    # Create tracked session in Supabase demo_sessions
    try:
        session_id = await create_call_session(
            call_control_id=call_control_id or "unknown",
            from_number=target_phone,
            session_type=session_type,
        )
    except Exception as e:
        logger.error(f"Error initializing call session: {e}")

    # Helper to send synthesized PCMU audio back in real-time chunks
    async def send_audio_in_chunks(audio_bytes: bytes):
        nonlocal stream_id, is_speaking
        is_speaking = True
        chunk_size = 160  # 20ms of PCMU at 8kHz
        start_time = asyncio.get_event_loop().time()

        try:
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i + chunk_size]
                base64_chunk = base64.b64encode(chunk).decode("utf-8")

                payload = {
                    "event": "media",
                    "media": {
                        "payload": base64_chunk
                    }
                }
                if stream_id:
                    payload["stream_id"] = stream_id

                await websocket.send_json(payload)

                # Drift-corrected sleep for natural 20ms pacing
                next_chunk_index = i + chunk_size
                expected_time = start_time + (next_chunk_index / 8000.0)
                now = asyncio.get_event_loop().time()
                sleep_duration = expected_time - now
                if sleep_duration > 0:
                    await asyncio.sleep(sleep_duration)

        except asyncio.CancelledError:
            logger.info("Playback cancelled by caller interruption / barge-in. Sending clear packet...")
            if stream_id:
                try:
                    await websocket.send_json({"event": "clear", "stream_id": stream_id})
                except Exception:
                    pass
            raise
        finally:
            is_speaking = False

    # Callback when Deepgram yields transcript segment
    async def on_transcript(transcript: str, is_final: bool):
        nonlocal playback_task, session_id, stream_id, is_speaking, is_processing, fast_greet_count, call_history

        try:
            clean_text = transcript.strip()
            if not clean_text:
                return

            # 1. INSTANT BARGE-IN: If bot is speaking and caller utters ANY word, stop bot immediately!
            if is_speaking or (playback_task and not playback_task.done()):
                logger.info(f"Instant Barge-in triggered by caller speaking: '{clean_text}'. Stopping speech...")
                if playback_task and not playback_task.done():
                    playback_task.cancel()
                is_speaking = False

                if stream_id:
                    try:
                        await websocket.send_json({"event": "clear", "stream_id": stream_id})
                    except Exception as e:
                        logger.warning(f"Error sending clear packet: {e}")

            # 2. Only process full reply once caller finishes utterance
            if not is_final:
                return

            logger.info(f"User Spoke (Final): '{clean_text}'")
            now_time = datetime.utcnow().strftime("%H:%M:%S")

            # Track caller utterance in session transcript
            if session_id:
                asyncio.create_task(append_call_transcript(session_id, "caller", clean_text, now_time))

            user_clean_lower = clean_text.lower().strip("?.!, ")

            # 3. FAST-PATH GREETING ACKNOWLEDGMENT:
            GREETING_PHRASES = (
                "hello", "hi", "hey", "can you hear me", "are you there",
                "hello hello", "yes hello", "am i audible", "i am audible",
                "i'm audible", "hearing me", "you hear me", "is someone there"
            )
            if user_clean_lower in GREETING_PHRASES:
                fast_greet_count += 1
                if fast_greet_count == 1:
                    reply_text = "Hey! Yes, I can hear you loud and clear. How can I help you out today?"
                else:
                    reply_text = "Yep, still right here with you! Hearing you loud and clear. Go ahead."

                call_history.append({"role": "user", "content": clean_text})
                call_history.append({"role": "assistant", "content": reply_text})

                logger.info(f"Fast-path greeting acknowledged: '{reply_text}'")
                if session_id:
                    asyncio.create_task(append_call_transcript(session_id, "agent", reply_text, datetime.utcnow().strftime("%H:%M:%S")))

                audio_bytes = await text_to_speech_pcmu(reply_text)
                if audio_bytes:
                    playback_task = asyncio.create_task(send_audio_in_chunks(audio_bytes))
                    try:
                        await playback_task
                    except asyncio.CancelledError:
                        pass
                return

            # 4. INTENT DETECTION FOR TRANSFER TO ZEESHAN
            transfer_intent_phrases = [
                "talk to zeeshan", "speak to zeeshan", "speak with zeeshan",
                "connect me to zeeshan", "connect me with zeeshan", "transfer me to zeeshan",
                "put me through to zeeshan", "i want zeeshan", "get me zeeshan",
                "talk to human", "speak to human", "talk with human", "speak with human",
                "talk to a human", "speak to a human", "talk with a human", "speak with a human",
                "talk to a person", "speak to a person", "connect me to a person",
                "transfer me", "forward my call", "representative", "operator"
            ]
            user_transfer_intent = any(phrase in user_clean_lower for phrase in transfer_intent_phrases)

            # 5. GENERATE AI RESPONSE (Sub-second, human, context-aware)
            is_processing = True
            try:
                reply_text = await ai_service.process_user_query(
                    wa_id=target_phone,
                    prompt=clean_text,
                    is_voice=True,
                    call_history=call_history
                )
                logger.info(f"AI Response: '{reply_text}'")
            finally:
                is_processing = False

            call_history.append({"role": "user", "content": clean_text})
            call_history.append({"role": "assistant", "content": reply_text})
            if len(call_history) > 14:
                call_history = call_history[-14:]

            # Track AI reply in session transcript
            if session_id:
                asyncio.create_task(append_call_transcript(session_id, "agent", reply_text, datetime.utcnow().strftime("%H:%M:%S")))

            ai_lower = reply_text.lower()
            ai_transfer_indicators = [
                "transfer you to zeeshan", "transferring you to zeeshan",
                "connect you with zeeshan", "connecting you with zeeshan",
                "transfer you now", "connecting you now", "transfer you", "transferring you"
            ]
            ai_transfer_intent = any(phrase in ai_lower for phrase in ai_transfer_indicators)
            should_transfer = user_transfer_intent or ai_transfer_intent

            if should_transfer:
                logger.info("Transfer intent confirmed. Notifying caller and transferring call...")
                if not ai_transfer_intent:
                    reply_text = "Sure thing, hold on just a second while I connect you right over to Zeeshan."

                audio_bytes = await text_to_speech_pcmu(reply_text)
                if audio_bytes:
                    playback_task = asyncio.create_task(send_audio_in_chunks(audio_bytes))
                    try:
                        await playback_task
                    except asyncio.CancelledError:
                        pass

                if call_control_id:
                    await telnyx_client.transfer_call(call_control_id, settings.FORWARDING_TARGET)
                    if session_id:
                        duration_sec = int(time.time() - call_start_time)
                        asyncio.create_task(end_call_session(session_id, duration_sec, status="transferred"))
                return

            # 6. SYNTHESIZE TO SPEECH VIA NATURAL DEEPGRAM AURA TTS
            audio_bytes = await text_to_speech_pcmu(reply_text)
            if audio_bytes:
                playback_task = asyncio.create_task(send_audio_in_chunks(audio_bytes))
                try:
                    await playback_task
                except asyncio.CancelledError:
                    logger.info("Playback of audio reply was cancelled.")
                    return

        except Exception as exc:
            logger.error(f"Fatal exception inside on_transcript: {exc}", exc_info=True)

    # Initialize and connect Deepgram Live client
    deepgram_client = DeepgramLiveClient(on_transcript_received=on_transcript)
    connected = await deepgram_client.connect()
    if not connected:
        logger.error("Could not establish Deepgram connection. Aborting WebSocket stream.")
        await websocket.close()
        return

    try:
        while True:
            # Receive streaming messages from Telnyx
            message = await websocket.receive_text()
            data = json.loads(message)
            event_type = data.get("event")

            if "stream_id" in data:
                stream_id = data.get("stream_id")

            if event_type == "media":
                media_data = data.get("media", {})
                payload = media_data.get("payload")
                if payload:
                    audio_bytes = base64.b64decode(payload)
                    await deepgram_client.send_audio(audio_bytes)

            elif event_type == "start":
                logger.info(f"Start streaming payload: {data}")
                async def play_initial_greeting():
                    nonlocal playback_task, session_id

                    # Differentiate greeting between Outbound pitch vs Inbound welcome
                    if direction in ("outgoing", "outbound"):
                        greeting_text = (
                            custom_outbound_prompt.strip()
                            if (custom_outbound_prompt and custom_outbound_prompt.strip())
                            else "Hi there! This is Sophia from Astraventa. I'm following up regarding your AI automation inquiry. Did I catch you at a good time?"
                        )
                    else:
                        greeting_text = "Hey there! Thanks for calling Astraventa. How can I help you out today?"

                    call_history.append({"role": "assistant", "content": greeting_text})
                    if session_id:
                        asyncio.create_task(append_call_transcript(session_id, "agent", greeting_text, datetime.utcnow().strftime("%H:%M:%S")))

                    audio_bytes = await text_to_speech_pcmu(greeting_text)
                    if audio_bytes:
                        playback_task = asyncio.create_task(send_audio_in_chunks(audio_bytes))
                        try:
                            await playback_task
                            logger.info(f"Finished streaming initial greeting ({direction}): '{greeting_text[:40]}...'")
                        except asyncio.CancelledError:
                            logger.info("Initial greeting playback was cancelled.")

                asyncio.create_task(play_initial_greeting())
            else:
                logger.info(f"Received Telnyx stream event: {data}")

    except WebSocketDisconnect:
        logger.info("Telnyx media WebSocket disconnected.")
    except Exception as e:
        logger.error(f"Error in Telnyx media streaming WebSocket: {e}", exc_info=True)
    finally:
        # Wrap up call session
        duration_sec = int(time.time() - call_start_time)
        if session_id:
            try:
                await end_call_session(session_id, duration_sec, status="completed")
            except Exception as e:
                logger.error(f"Error ending call session: {e}")

        if playback_task and not playback_task.done():
            playback_task.cancel()
        if deepgram_client:
            await deepgram_client.close()
        logger.info(f"Voice streaming session {session_id} closed (Total duration: {duration_sec}s).")
