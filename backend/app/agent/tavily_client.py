"""Minimal Tavily search client (live web search for job postings)."""
from __future__ import annotations

from typing import Any

import requests

from ..config import get_settings

TAVILY_URL = "https://api.tavily.com/search"


class TavilyClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.tavily_enabled

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        if not self.settings.tavily_enabled:
            raise RuntimeError("Tavily is not configured (TAVILY_API_KEY missing).")
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
        }
        resp = requests.post(TAVILY_URL, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json().get("results", [])
