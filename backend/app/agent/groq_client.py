"""Thin wrapper around the Groq API that always returns parsed JSON.

Groq exposes an OpenAI-compatible chat-completions endpoint at
``https://api.groq.com/openai/v1``. We call it directly with ``requests`` and
ask for a JSON object response, so no extra SDK dependency is required.

The client retries transient failures (HTTP 429 rate limits and 5xx errors),
honouring the ``Retry-After`` header, and raises an informative error that
includes Groq's response body so failures are easy to diagnose.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

from ..config import get_settings

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 4


def _strip_fences(text: str) -> str:
    text = _FENCE_RE.sub("", text.strip())
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    return match.group(1) if match else text


class GroqClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._api_key = self.settings.groq_api_key or None

    @property
    def enabled(self) -> bool:
        return self._api_key is not None

    def generate_json(self, system_prompt: str, user_content: str) -> dict[str, Any]:
        """Call Groq and parse the response as JSON. Raises on failure."""
        if self._api_key is None:
            raise RuntimeError("Groq is not configured (GROQ_API_KEY missing).")

        url = f"{self.settings.groq_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.settings.groq_model,
            "temperature": 0.3,
            # Bound the completion so long answers can't get truncated into
            # invalid JSON. 8k is plenty for our largest node (skill-gap).
            "max_tokens": 8192,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }

        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = requests.post(url, headers=headers, json=body, timeout=120)
            except requests.RequestException as exc:  # network hiccup
                last_error = exc
                time.sleep(min(2 ** attempt, 8))
                continue

            if response.status_code in _RETRY_STATUSES and attempt < _MAX_RETRIES - 1:
                # Respect Groq's Retry-After hint for rate limits when present.
                wait = response.headers.get("retry-after")
                delay = float(wait) if wait and wait.replace(".", "", 1).isdigit() else min(2 ** attempt, 8)
                time.sleep(delay)
                continue

            if response.status_code != 200:
                # Surface Groq's actual error message (e.g. rate limit,
                # context-length, model-not-found) instead of a bare HTTPError.
                raise RuntimeError(
                    f"Groq API error {response.status_code} for model "
                    f"'{self.settings.groq_model}': {response.text}"
                )

            data = response.json()
            raw = (data["choices"][0]["message"]["content"] or "").strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return json.loads(_strip_fences(raw))

        raise RuntimeError(f"Groq request failed after {_MAX_RETRIES} attempts: {last_error}")
