from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "cccd": r"\b\d{12}\b",  # Must come before phone_vn to avoid partial overlap
    "phone_vn": r"(?:\+84|0)(?:\d{2,3}[\s\.\-]\d{3}[\s\.\-]\d{3,4}|\d{9,10})",  # 0901234567, 090 123 4567, 090.123.4567
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "passport": r"\b[A-Z]\d{7}\b",
    "address_vn": r"\d+\s[\w\s]+,?\s*(?:phường|xã|thị trấn|quận|huyện|thị xã|thành phố|tỉnh)\s+[\w\s]+",
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
