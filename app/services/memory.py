import logging
from typing import List, Dict, Any
from app.config import settings
from app import services

logger = logging.getLogger("memory_manager")


class ChatMemoryManager:
    """
    Persistent conversation memory manager using Supabase PostgreSQL `chat_logs`.
    Falls back to RAM if database connection is unavailable.
    """

    def __init__(self, max_turns: int = settings.MAX_MEMORY_TURNS):
        self.max_turns = max_turns
        self._ram_fallback: Dict[str, List[Dict[str, str]]] = {}

    async def get_history_async(self, wa_id: str) -> List[Dict[str, str]]:
        """Asynchronously retrieves chat history from Supabase or RAM fallback."""
        try:
            from app.services.db import fetch_chat_history
            history = await fetch_chat_history(wa_id=wa_id, limit=self.max_turns)
            if history:
                return history
        except Exception as exc:
            logger.warning(f"Failed to fetch history from DB for {wa_id}: {exc}")

        return self._ram_fallback.get(wa_id, []).copy()

    def get_history(self, wa_id: str) -> List[Dict[str, str]]:
        """Synchronous wrapper for history retrieval (using RAM cache or empty list)."""
        return self._ram_fallback.get(wa_id, []).copy()

    async def add_user_message(self, wa_id: str, text: str) -> None:
        """Saves user message to Supabase DB and RAM cache."""
        # Update RAM fallback
        if wa_id not in self._ram_fallback:
            self._ram_fallback[wa_id] = []
        self._ram_fallback[wa_id].append({"role": "user", "content": text})
        self._trim_ram(wa_id)

        # Save to Supabase DB
        try:
            from app.services.db import save_chat_message
            await save_chat_message(wa_id=wa_id, role="user", content=text)
        except Exception as exc:
            logger.error(f"Error persisting user message to DB: {exc}")

    async def add_ai_message(self, wa_id: str, text: str) -> None:
        """Saves AI response message to Supabase DB and RAM cache."""
        # Update RAM fallback
        if wa_id not in self._ram_fallback:
            self._ram_fallback[wa_id] = []
        self._ram_fallback[wa_id].append({"role": "assistant", "content": text})
        self._trim_ram(wa_id)

        # Save to Supabase DB
        try:
            from app.services.db import save_chat_message
            await save_chat_message(wa_id=wa_id, role="assistant", content=text)
        except Exception as exc:
            logger.error(f"Error persisting AI message to DB: {exc}")

    async def clear_history_async(self, wa_id: str) -> None:
        """Clears memory for wa_id."""
        if wa_id in self._ram_fallback:
            self._ram_fallback[wa_id] = []

    def clear_history(self, wa_id: str) -> None:
        """Synchronous clear memory."""
        if wa_id in self._ram_fallback:
            self._ram_fallback[wa_id] = []

    def _trim_ram(self, wa_id: str) -> None:
        max_messages = self.max_turns * 2
        if wa_id in self._ram_fallback and len(self._ram_fallback[wa_id]) > max_messages:
            self._ram_fallback[wa_id] = self._ram_fallback[wa_id][-max_messages:]


memory_manager = ChatMemoryManager()
