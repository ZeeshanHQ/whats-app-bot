from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    META_API_VERSION: str = "v25.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WEBHOOK_VERIFY_TOKEN: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    GEMINI_MODEL: str = "google/gemini-2.5-flash:free"
    MAX_MEMORY_TURNS: int = 10
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    TELNYX_API_KEY: str = ""
    TELNYX_CONNECTION_ID: str = "3011985982435100116"
    TELNYX_PHONE_NUMBER: str = "+19255040101"
    DEEPGRAM_API_KEY: str = ""
    FORWARDING_TARGET: str = ""

    # LiveKit & Voice Platform Keys
    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""
    GROQ_API_KEY: str = ""
    CARTESIA_API_KEY: str = ""
    LIVEKIT_SIP_TRUNK_ID: str = ""
    SERVER_DOMAIN: str = "api.engine.astraventa.com"

    @property
    def GRAPH_API_URL(self) -> str:
        return f"https://graph.facebook.com/{self.META_API_VERSION}/{self.WHATSAPP_PHONE_NUMBER_ID}/messages"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
