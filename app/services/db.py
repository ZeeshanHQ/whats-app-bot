import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from app.config import settings

logger = logging.getLogger("db_service")

supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """Returns singleton Supabase client instance."""
    global supabase_client
    if supabase_client is not None:
        return supabase_client

    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            opts = ClientOptions(postgrest_client_timeout=10)
            supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY, options=opts)
            logger.info(f"Supabase client initialized for: {settings.SUPABASE_URL}")
            return supabase_client
        except Exception as exc:
            logger.error(f"Failed to initialize Supabase client: {exc}")
            try:
                supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                return supabase_client
            except Exception as exc2:
                logger.error(f"Secondary Supabase init failed: {exc2}")

    return None


async def save_chat_message(wa_id: str, role: str, content: str) -> None:
    """Inserts a chat log message row into `chat_logs` table in Supabase."""
    client = get_supabase_client()
    if not client:
        logger.warning("Supabase client not available. Skipping chat log persistence.")
        return

    try:
        data = {
            "wa_id": wa_id,
            "role": role,
            "content": content,
        }
        res = client.table("chat_logs").insert(data).execute()
        logger.debug(f"Saved chat message for {wa_id} ({role}): {res.data}")
    except Exception as exc:
        logger.error(f"Error saving chat message for {wa_id}: {exc}")


async def fetch_chat_history(wa_id: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Retrieves the last `limit` conversation turns for wa_id from `chat_logs` table,
    ordered chronologically. Returns list of {"role": str, "content": str}.
    """
    client = get_supabase_client()
    if not client:
        return []

    try:
        max_messages = limit * 2
        res = (
            client.table("chat_logs")
            .select("role, content, created_at")
            .eq("wa_id", wa_id)
            .order("created_at", desc=True)
            .limit(max_messages)
            .execute()
        )

        rows = res.data or []
        rows.reverse()

        return [{"role": r["role"], "content": r["content"]} for r in rows]

    except Exception as exc:
        logger.error(f"Error fetching chat history for {wa_id}: {exc}")
        return []


async def search_knowledge_base(
    query_embedding: List[float],
    match_threshold: float = 0.3,
    match_count: int = 3,
) -> List[Dict[str, Any]]:
    """
    Executes PostgreSQL RPC `match_knowledge_base` similarity search against vectors.
    """
    client = get_supabase_client()
    if not client or not query_embedding:
        return []

    try:
        params = {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
        }
        res = client.rpc("match_knowledge_base", params).execute()
        return res.data or []

    except Exception as exc:
        logger.error(f"Error searching knowledge base: {exc}")
        return []


async def seed_knowledge_base(content: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
    """Inserts a knowledge document with vector embedding into `knowledge_base` table."""
    client = get_supabase_client()
    if not client:
        return

    try:
        data = {
            "content": content,
            "embedding": embedding,
            "metadata": metadata or {},
        }
        client.table("knowledge_base").insert(data).execute()
        logger.info(f"Seeded knowledge base document: {content[:50]}...")
    except Exception as exc:
        logger.error(f"Error seeding knowledge base: {exc}")
