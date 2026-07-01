"""Runtime configuration loaded from environment variables."""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
        self.tavily_api_key: str = os.getenv("TAVILY_API_KEY", "").strip()
        self.default_location: str = os.getenv("DEFAULT_LOCATION", "Remote").strip()
        self.frontend_origins: list[str] = [
            o.strip()
            for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ]

    @property
    def groq_enabled(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def tavily_enabled(self) -> bool:
        return bool(self.tavily_api_key)

    @property
    def mock_mode(self) -> bool:
        # Without a Groq key we can't do real reasoning, so the pipeline falls
        # back to deterministic sample data — the full flow still runs for a demo.
        return not self.groq_enabled


@lru_cache
def get_settings() -> Settings:
    return Settings()
