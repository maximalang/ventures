from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

SENSITIVE_KEY = re.compile(r"(?i)(secret|token|password|passwd|api[_-]?key|authorization|cookie|credential|private[_-]?key)")
SENSITIVE_VALUE = re.compile(r"(?i)(bearer\s+[a-z0-9._~+/=-]+|(?:sk|ghp|github_pat)-?[a-z0-9_-]{12,})")
REDACTED = "[REDACTED]"


def redact(value: Any, *, key: str = "") -> Any:
    if SENSITIVE_KEY.search(key):
        return REDACTED
    if isinstance(value, Mapping):
        return {str(k): redact(v, key=str(k)) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return SENSITIVE_VALUE.sub(REDACTED, value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def stable_json(value: Any) -> str:
    return json.dumps(redact(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def args_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def stable_id(*parts: Any) -> str:
    return hashlib.sha256("\x1f".join(str(part or "") for part in parts).encode("utf-8")).hexdigest()
