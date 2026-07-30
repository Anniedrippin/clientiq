"""Groq LLM service — used for fast reasoning + executive report generation.

If GROQ_API_KEY isn't configured, falls back to a deterministic local
summarizer so the whole pipeline still runs end-to-end in a demo/offline
environment. Both paths log through the same template so the trace view
always shows an "llm_reasoning" step either way.
"""

import json
import httpx

from app.core.config import settings
from app.core.logging_config import get_logger, log_event, Timer

logger = get_logger(__name__)

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


class GroqService:
    def __init__(self):
        self.enabled = bool(settings.GROQ_API_KEY)
        log_event(logger, "groq_service_initialized", enabled=self.enabled, model=settings.GROQ_MODEL)

    def generate_json(self, system_prompt: str, user_prompt: str, fallback: dict) -> dict:
        """Calls Groq for a structured-JSON response. Falls back to a
        deterministic payload if no API key is set or the call fails,
        so the demo never breaks."""
        timer = Timer()
        log_event(logger, "llm_reasoning_started", model=settings.GROQ_MODEL, prompt_chars=len(user_prompt))

        if not self.enabled:
            log_event(
                logger,
                "llm_reasoning_skipped_no_api_key",
                level="warning",
                duration_ms=timer.ms(),
            )
            return fallback

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    GROQ_ENDPOINT,
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": settings.GROQ_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.2,
                    },
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                log_event(
                    logger,
                    "llm_reasoning_completed",
                    status="success",
                    duration_ms=timer.ms(),
                    tokens_used=resp.json().get("usage", {}).get("total_tokens"),
                )
                return parsed
        except Exception as exc:  # noqa: BLE001
            log_event(
                logger,
                "llm_reasoning_failed",
                level="error",
                status="error",
                error=str(exc),
                duration_ms=timer.ms(),
            )
            return fallback


groq_service = GroqService()
