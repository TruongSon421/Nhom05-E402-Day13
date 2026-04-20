from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .incidents import STATE


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


class FakeLLM:
    DEFAULT_MAX_TOKENS = 120  # Cost optimization: cap output tokens

    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model

    def generate(self, prompt: str, max_tokens: int | None = None) -> FakeResponse:
        time.sleep(0.15)
        input_tokens = max(20, len(prompt) // 4)
        cap = max_tokens if max_tokens is not None else self.DEFAULT_MAX_TOKENS
        output_tokens = min(random.randint(80, 180), cap)
        if STATE["cost_spike"]:
            output_tokens *= 4
        answer = (
            "Starter answer. Teams should improve this output logic and add better quality checks. "
            "Use retrieved context and keep responses concise."
        )
        return FakeResponse(text=answer, usage=FakeUsage(input_tokens, output_tokens), model=self.model)
