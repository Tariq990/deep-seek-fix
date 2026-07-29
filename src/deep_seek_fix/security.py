import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._\-]+"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[A-Za-z0-9._\-]+"),
    re.compile(r"\b(sk-[A-Za-z0-9_\-]{12,})\b"),
    re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{20,})\b"),
]


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: match.group(1) + "[REDACTED]", redacted)
    return redacted


def safe_output_hash(text: str) -> str:
    return sha256_text(redact_secrets(text))


def environment_fingerprint() -> str:
    relevant = {
        "pythonioencoding": os.environ.get("PYTHONIOENCODING", ""),
        "dsfix_live_tests": os.environ.get("DSFIX_ENABLE_LIVE_TESTS", "0"),
        "platform": os.name,
    }
    return sha256_text(canonical_json(relevant))


def contains_secret(text: str) -> bool:
    return redact_secrets(text) != text


def resolve_under(base: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True
