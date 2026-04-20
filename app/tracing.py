from __future__ import annotations

import os
from typing import Any

try:
    from langfuse.decorators import observe, langfuse_context  # v2 API

    def get_langfuse():
        return langfuse_context

except Exception:  # pragma: no cover
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None: pass
        def update_current_observation(self, **kwargs: Any) -> None: pass
        def flush(self) -> None: pass

    langfuse_context = _DummyContext()

    def get_langfuse():
        return langfuse_context


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
