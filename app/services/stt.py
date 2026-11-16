import asyncio
import logging
import json
from typing import Callable, Union, Awaitable
import websockets
from app.config import settings

logger = logging.getLogger("stt_service")

class DeepgramLiveClient:
    """
    Manages a real-time Speech-to-Text WebSocket connection with Deepgram.
    Pipes 8kHz G.711 μ-law (mulaw) audio stream to Deepgram and invokes callback on transcripts.
    """
    def __init__(self, on_transcript_received: Callable[[str, bool], Union[None, Awaitable[None]]]):
        self.api_key = settings.DEEPGRAM_API_KEY
        # encoding=mulaw, sample_rate=8000, channels=1 matching Telnyx RTP stream
        # interim_results=true allows word-by-word streaming for real-time barge-in
        # endpointing=650 detects natural pauses in speech (650ms) to prevent cutting caller off mid-thought
        # utterance_end_ms=1200 marks turn boundaries cleanly
        # model=nova-2 provides state-of-the-art transcription accuracy for phone calls
        # smart_format=true formats numbers, capitalization, and names like Zeeshan correctly
        # keywords boosts recognition of company terms
        self.url = (
            "wss://api.deepgram.com/v1/listen?"
            "encoding=mulaw&sample_rate=8000&channels=1&"
            "interim_results=true&endpointing=650&utterance_end_ms=1200&"
            "model=nova-2&smart_format=true&"
            "keywords=Astraventa:3&keywords=Zeeshan:3&keywords=services:2&keywords=pricing:2&keywords=voice:2&keywords=website:2"
        )
        self.on_transcript = on_transcript_received
        self.websocket = None
        self.receive_task = None
        self.is_active = False

    async def connect(self) -> bool:
        if not self.api_key:
            logger.error("DEEPGRAM_API_KEY not configured in environment settings.")
            return False
        try:
            logger.info(f"Connecting to Deepgram Live STT: {self.url}")
            headers = {"Authorization": f"Token {self.api_key}"}
            self.websocket = await websockets.connect(
                self.url,
                additional_headers=headers,
                ping_interval=10,
                ping_timeout=10
            )
            self.is_active = True
            self.receive_task = asyncio.create_task(self._receive_loop())
            logger.info("Successfully connected to Deepgram Live STT.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram Live STT: {e}", exc_info=True)
            self.is_active = False
            return False

    async def send_audio(self, chunk: bytes):
        if self.websocket and self.is_active:
            try:
                await self.websocket.send(chunk)
            except Exception as e:
                logger.error(f"Error sending audio chunk to Deepgram: {e}")
                await self.close()

    async def _receive_loop(self):
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    if not isinstance(data, dict):
                        continue

                    # Filter out metadata or heartbeat messages
                    msg_type = data.get("type")
                    if msg_type in ("Metadata", "UtteranceEnd", "SpeechStarted"):
                        continue

                    channel = data.get("channel")
                    if isinstance(channel, list) and len(channel) > 0:
                        channel = channel[0]
                    elif not isinstance(channel, dict):
                        continue

                    alternatives = channel.get("alternatives")
                    if not alternatives or not isinstance(alternatives, list):
                        continue

                    first_alt = alternatives[0]
                    if not isinstance(first_alt, dict):
                        continue

                    transcript = first_alt.get("transcript", "").strip()
                    is_final = data.get("is_final", False)
                    speech_final = data.get("speech_final", False)

                    # Trigger callback when a speech segment is transcribed
                    if transcript:
                        final_flag = is_final or speech_final
                        if asyncio.iscoroutinefunction(self.on_transcript):
                            await self.on_transcript(transcript, final_flag)
                        else:
                            self.on_transcript(transcript, final_flag)

                except Exception as inner_err:
                    logger.error(f"Error handling Deepgram transcript: {inner_err}", exc_info=True)
                    continue

        except websockets.exceptions.ConnectionClosed:
            logger.info("Deepgram WebSocket connection closed cleanly by server.")
        except Exception as e:
            logger.error(f"Fatal error in Deepgram receive loop: {e}", exc_info=True)
        finally:
            self.is_active = False

    async def close(self):
        self.is_active = False
        if self.websocket:
            try:
                # Send empty json close stream command to Deepgram
                await self.websocket.send(json.dumps({"type": "CloseStream"}))
                await self.websocket.close()
            except Exception:
                pass
            self.websocket = None
        if self.receive_task:
            self.receive_task.cancel()
            self.receive_task = None
        logger.info("Deepgram STT connection closed.")
