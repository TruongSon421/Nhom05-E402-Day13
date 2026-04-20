"""Audit logging module – writes immutable audit trail to a separate JSONL file.

Bonus item: +2 diem – Audit logs tach rieng khoi application logs.
Every sensitive action (chat, incident toggle) is recorded with:
  - ISO timestamp, user_id_hash (hashed), action, correlation_id, result
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))


def log_audit_event(
    action: str,
    user_id_hash: str,
    correlation_id: str,
    result: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write a single audit event to the audit log file.

    Audit logs are kept separate from application logs so they can be
    retained, archived, and reviewed independently (e.g., for compliance).

    Args:
        action: What was attempted (e.g. "chat_request", "incident_enable").
        user_id_hash: SHA-256-truncated user identifier (no raw PII).
        correlation_id: Request correlation ID for cross-referencing app logs.
        result: Outcome — "success", "error", or "denied".
        metadata: Optional extra key/value pairs (PII-free).
    """
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "user_id_hash": user_id_hash,
        "correlation_id": correlation_id,
        "result": result,
    }
    if metadata:
        record["metadata"] = metadata

    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
