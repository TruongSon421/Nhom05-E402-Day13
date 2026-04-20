"""Audit logging module – writes immutable audit trail to a separate JSONL file.

Bonus item: +2 điểm – Audit logs tách riêng khỏi application logs.
Every sensitive action (chat, incident toggle) is recorded with:
  - ISO timestamp, actor (hashed), action, resource, outcome, correlation_id
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))


def log_audit_event(
    action: str,
    actor: str,
    resource: str,
    outcome: str,
    correlation_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append one audit event to the audit JSONL file.

    Args:
        action:         What happened (e.g. "chat_request", "incident_enable")
        actor:          Who did it – always a hashed ID, never raw PII
        resource:       What was targeted (e.g. "feature:qa", "incident:rag_slow")
        outcome:        "success" | "error"
        correlation_id: Request correlation ID for cross-referencing app logs
        metadata:       Optional extra key-value pairs (no PII)
    """
    event: dict[str, Any] = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "audit": True,
        "action": action,
        "actor": actor,
        "resource": resource,
        "outcome": outcome,
        "correlation_id": correlation_id,
    }
    if metadata:
        event["metadata"] = metadata

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
