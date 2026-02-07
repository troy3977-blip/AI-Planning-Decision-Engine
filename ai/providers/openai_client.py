# ai/providers/openai_client.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from config.settings import settings
from ai.reasoning import LLMClient


@dataclass(frozen=True)
class OpenAIClientConfig:
    """
    Optional overrides. Defaults come from config.settings.Settings (.env / env vars).
    """
    model: Optional[str] = None
    temperature: float = 0.2


class OpenAIClient(LLMClient):
    """
    Provider adapter that returns raw JSON text for strict parsing upstream.

    - Uses OpenAI Responses API
    - Forces JSON-only output (json_object)
    - Returns ONLY the JSON object as a string (no markdown)
    """

    def __init__(self, config: Optional[OpenAIClientConfig] = None):
        self.config = config or OpenAIClientConfig()

        # Central config (supports .env via pydantic-settings)
        api_key = settings.openai_api_key
        model = self.config.model or settings.openai_model

        if not api_key:
            raise ValueError("Missing OpenAI API key (OPENAI_API_KEY).")

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def complete_json(self, *, system: str, user: str) -> str:
        """
        Returns ONLY the model's JSON object as a string.
        Upstream enforces strict { ... } parsing.
        """
        resp = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # Enforce machine-readable JSON output
            text={"format": {"type": "json_object"}},
            temperature=self.config.temperature,
        )

        out = (resp.output_text or "").strip()
        if not out:
            raise RuntimeError("OpenAI returned empty output_text.")
        return out