# ai/providers/openai_client.py (only the init changes)
from __future__ import annotations
from config.settings import settings
from openai import OpenAI
import os
from dataclasses import dataclass
from typing import Optional
from ..reasoning import LLMClient

class OpenAIClient(LLMClient):
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

@dataclass
class OpenAIClientConfig:
    """
    Minimal config for an OpenAI provider adapter.

    Environment variables (defaults):
      - OPENAI_API_KEY (required)
      - OPENAI_MODEL (optional) default: gpt-4.1-mini
    """
    api_key_env: str = "OPENAI_API_KEY"
    model_env: str = "OPENAI_MODEL"
    default_model: str = "gpt-4.1-mini"
    timeout_s: float = 30.0


class OpenAIClient(LLMClient):
    """
    Provider adapter that returns raw JSON text for strict parsing upstream.
    Uses the Responses API and requests a JSON object output.
    """

    def __init__(self, config: Optional[OpenAIClientConfig] = None):
        self.config = config or OpenAIClientConfig()
        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            raise ValueError(
                f"Missing OpenAI API key. Set env var: {self.config.api_key_env}"
            )
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv(self.config.model_env, self.config.default_model)

    def complete_json(self, *, system: str, user: str) -> str:
        """
        Return ONLY the model's JSON object as a string (no markdown).
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
            # Keep outputs tight & deterministic-ish for decision support
            temperature=0.2,
        )

        # The SDK returns aggregated output text at resp.output_text
        out = (resp.output_text or "").strip()
        if not out:
            raise RuntimeError("OpenAI returned empty output_text.")
        return out
    