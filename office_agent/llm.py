"""Thin wrapper around the Anthropic API, imported lazily.

Nothing else in this package imports `anthropic` at module load time, so
kb search and rule-based triage work with zero API key and zero network
access. Only drafting a reply (email_triage.drafting) needs an LLMClient.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

DEFAULT_MODEL = "claude-sonnet-5"


class LLMClient(Protocol):
    def complete(self, system: str, prompt: str) -> str: ...


@dataclass
class AnthropicClient:
    model: str = DEFAULT_MODEL
    api_key: str | None = None

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it or pass api_key= explicitly "
                "before drafting LLM-based replies."
            )

    def complete(self, system: str, prompt: str) -> str:
        import anthropic  # lazy import — optional dependency

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
