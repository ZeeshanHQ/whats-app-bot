import logging
import re
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.services.memory import memory_manager
from app.services.db import search_knowledge_base

logger = logging.getLogger("ai_brain")

BASE_SYSTEM_INSTRUCTION = (
    "You are strictly the official AI Assistant for Astraventa, a technology agency specializing in "
    "agentic workflows, custom AI backends, automation, web engineering, UI/UX, and enterprise systems. "
    "NEVER describe yourself as a general language model or list generic AI capabilities like translation or math "
    "unless specifically relevant to Astraventa's agency services. "
    "Always keep responses tailored strictly to Astraventa's agency capabilities. "
    "When a client asks to book a meeting, schedule a call, or contact Astraventa, always provide: "
    "• Direct Call: +1 925 504 0101\n"
    "• Book Consultation (Calendly): https://calendly.com/astraventaai/15-min-technical-walkthrough-astraventa?month=2026-07\n"
    "Be direct, professional, concise, and structured for WhatsApp/mobile chat. "
    "Keep replies under 250 words."
)


def clean_whatsapp_formatting(text: str) -> str:
    """
    Cleans up AI text output formatting for native WhatsApp markdown rendering:
    1. Fix '* *Bold text*' -> '• *Bold text*'
    2. Fix nested bold/bullet anomalies like '*1. *Bold*' -> '1. *Bold*'
    3. Clean up remaining double asterisks '**Bold**' -> '*Bold*'
    """
    if not text:
        return ""

    # 1. Fix "* *Bold text*" -> "• *Bold text*"
    text = re.sub(r'^\*\s+\*([^*]+)\*', r'• *\1*', text, flags=re.MULTILINE)
    # 2. Fix nested bold/bullet anomalies like "*1. *Bold*" -> "1. *Bold*"
    text = re.sub(r'^\*\s*(\d+\.)', r'\1', text, flags=re.MULTILINE)
    # 3. Clean up any remaining double asterisks "**Bold**" -> "*Bold*"
    text = text.replace("**", "*")

    return text.strip()


class GeminiAIService:
    """
    AI Service with Vector Search RAG (Retrieval-Augmented Generation), Supabase persistence,
    Strict Astraventa Persona Alignment, and Native WhatsApp Formatting.
    """

    def __init__(self):
        self.model = settings.GEMINI_MODEL

    async def detect_intent(self, prompt: str) -> str:
        """
        Analyzes user input prompt to classify intent for interactive actions:
        Returns: 'pricing', 'services', 'book_call', 'show_options', or 'general_chat'
        """
        p_lower = prompt.lower()
        if any(w in p_lower for w in ["price", "pricing", "cost", "package", "rate", "fee", "how much"]):
            return "pricing"
        if any(w in p_lower for w in ["service", "services", "offer", "what do you do", "capabilities", "web", "design", "app"]):
            return "services"
        if any(w in p_lower for w in ["book", "call", "schedule", "demo", "contact", "consultation", "talk"]):
            return "book_call"
        if any(w in p_lower for w in ["option", "options", "menu", "help", "start", "list"]):
            return "show_options"
        return "general_chat"

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generates 768-dimensional vector embedding using google-genai or OpenRouter API.
        """
        if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("sk-or-v1-"):
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                res = await client.aio.models.embed_content(
                    model="text-embedding-004",
                    contents=text,
                )
                if res and res.embedding and res.embedding.values:
                    return list(res.embedding.values)
            except Exception as exc:
                logger.warning(f"google-genai embedding failed: {exc}")

        api_key = settings.OPENROUTER_API_KEY or settings.GEMINI_API_KEY
        if api_key:
            try:
                url = "https://openrouter.ai/api/v1/embeddings"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "google/text-embedding-004",
                    "input": text,
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        embeddings = data.get("data", [{}])[0].get("embedding")
                        if embeddings:
                            return embeddings
            except Exception as exc:
                logger.warning(f"OpenRouter embedding failed: {exc}")

        return None

    async def _retrieve_rag_context(self, prompt: str) -> str:
        """Retrieves relevant company knowledge from Supabase vector search."""
        try:
            embedding = await self.generate_embedding(prompt)
            if not embedding:
                return ""

            matches = await search_knowledge_base(
                query_embedding=embedding,
                match_threshold=0.1,
                match_count=4,
            )

            if not matches:
                return ""

            context_snippets = []
            for item in matches:
                snippet = item.get("content", "").strip()
                if snippet:
                    context_snippets.append(f"- {snippet}")

            if context_snippets:
                joined_snippets = "\n".join(context_snippets)
                logger.info(f"Retrieved RAG Knowledge Snippets:\n{joined_snippets}")
                return f"\n\nRelevant Astraventa Company Knowledge:\n{joined_snippets}"

        except Exception as exc:
            logger.error(f"Error during RAG context retrieval: {exc}")

        return ""

    async def _generate_via_google_genai(
        self, prompt: str, history: List[Dict[str, str]], system_instruction: str
    ) -> Optional[str]:
        """Attempt generation via google-genai SDK."""
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("sk-or-v1-"):
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            contents = []
            for item in history:
                role = "user" if item["role"] == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=item["content"])]
                ))

            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            ))

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )

            response = await client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            if response and response.text:
                return clean_whatsapp_formatting(response.text)
            return None

        except Exception as exc:
            logger.warning(f"google-genai SDK generation failed: {exc}")
            return None

    async def _generate_via_openrouter(
        self, prompt: str, history: List[Dict[str, str]], system_instruction: str
    ) -> str:
        """Attempt generation via OpenRouter API with multi-model fallback."""
        api_key = settings.OPENROUTER_API_KEY or settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("No valid GEMINI_API_KEY or OPENROUTER_API_KEY provided.")

        messages = [{"role": "system", "content": system_instruction}]

        for item in history:
            role = "user" if item["role"] == "user" else "assistant"
            messages.append({"role": role, "content": item["content"]})

        messages.append({"role": "user", "content": prompt})

        # Candidate models list
        candidate_models = [
            "google/gemini-2.5-flash",
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-r1:free",
            "google/gemini-2.0-flash-exp:free",
        ]

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://astraventa.com",
            "X-Title": "Astraventa WhatsApp Bot",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            for model_name in candidate_models:
                try:
                    payload = {
                        "model": model_name,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1000,
                    }
                    response = await client.post(url, json=payload, headers=headers)
                    res_json = response.json()

                    if response.status_code == 200:
                        choices = res_json.get("choices", [])
                        if choices and choices[0].get("message"):
                            raw_reply = choices[0]["message"]["content"]
                            logger.info(f"OpenRouter generation successful with model: {model_name}")
                            return clean_whatsapp_formatting(raw_reply)
                    else:
                        logger.warning(f"OpenRouter model '{model_name}' failed [{response.status_code}]: {res_json}")
                except Exception as exc:
                    logger.warning(f"OpenRouter request to '{model_name}' exception: {exc}")

        raise RuntimeError("All OpenRouter models failed to respond.")

    async def process_user_query(self, wa_id: str, prompt: str) -> str:
        """
        1. Fetch history from Supabase DB memory.
        2. Perform Vector Search (RAG) against `knowledge_base`.
        3. Inject RAG context into system prompt.
        4. Call Gemini AI generation.
        5. Format clean WhatsApp markdown.
        6. Persist user input & AI response into Supabase `chat_logs`.
        """
        history = await memory_manager.get_history_async(wa_id)
        rag_context = await self._retrieve_rag_context(prompt)
        full_system_instruction = BASE_SYSTEM_INSTRUCTION + rag_context

        try:
            ai_reply = await self._generate_via_google_genai(prompt, history, full_system_instruction)
            if not ai_reply:
                ai_reply = await self._generate_via_openrouter(prompt, history, full_system_instruction)

            await memory_manager.add_user_message(wa_id, prompt)
            await memory_manager.add_ai_message(wa_id, ai_reply)

            return ai_reply

        except Exception as exc:
            logger.error(f"AI Generation Error for wa_id {wa_id}: {exc}", exc_info=True)
            fallback_msg = (
                "Sorry, I am currently experiencing technical difficulties processing your request. "
                "Please try again shortly!"
            )
            return fallback_msg

    async def process_audio_query(self, wa_id: str, audio_bytes: Optional[bytes], mime_type: str = "audio/ogg") -> str:
        """
        Processes WhatsApp voice notes / audio messages using Gemini 2.5 Multimodal Audio understanding.
        """
        if audio_bytes:
            try:
                if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("sk-or-v1-"):
                    from google import genai
                    from google.genai import types

                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    history = await memory_manager.get_history_async(wa_id)
                    rag_context = await self._retrieve_rag_context("Audio Query")
                    full_system_instruction = BASE_SYSTEM_INSTRUCTION + rag_context

                    contents = []
                    for item in history:
                        role = "user" if item["role"] == "user" else "model"
                        contents.append(types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=item["content"])]
                        ))

                    contents.append(types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type or "audio/ogg"),
                            types.Part.from_text(text="Listen carefully to this WhatsApp voice message and respond to the client's request as Astraventa's AI Assistant.")
                        ]
                    ))

                    config = types.GenerateContentConfig(
                        system_instruction=full_system_instruction,
                        temperature=0.7,
                        max_output_tokens=1000
                    )

                    res = await client.aio.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents,
                        config=config,
                    )
                    if res and res.text:
                        ai_reply = clean_whatsapp_formatting(res.text)
                        await memory_manager.add_user_message(wa_id, "[Voice Note Received]")
                        await memory_manager.add_ai_message(wa_id, ai_reply)
                        return ai_reply
            except Exception as exc:
                logger.warning(f"Audio processing exception: {exc}")

        # Intelligent Fallback response for voice notes
        fallback_prompt = "The user sent a WhatsApp voice message. Introduce Astraventa's services and offer to assist them or schedule a technical call."
        return await self.process_user_query(wa_id, fallback_prompt)


ai_service = GeminiAIService()
