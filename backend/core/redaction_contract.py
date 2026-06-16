"""
Public-safe redaction contract — describes required redaction categories and test vectors.

No internal telemetry server rules. Implementation is local preview only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

CONTRACT_VERSION = 1

REDACTION_CATEGORIES = (
    "ipv4",
    "mac_address",
    "ipv6",
    "email",
    "user_home_path",
    "api_token",
    "jwt_like",
    "ssh_key_marker",
)

_PLACEHOLDER = "[REDACTED]"

_PATTERNS: dict[str, re.Pattern[str]] = {
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "ipv6": re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b"),
    "mac_address": re.compile(r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "user_home_path": re.compile(r"(?:/home|/Users)/[^\s/]+"),
    "api_token": re.compile(r"\b(?:ghp_|sk-[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{16})\S*\b"),
    "jwt_like": re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
    "ssh_key_marker": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


@dataclass(frozen=True)
class RedactionResult:
    """Normalized redaction preview result."""

    original_length: int
    redacted_text: str
    categories_matched: tuple[str, ...]
    contract_version: int = CONTRACT_VERSION


# Public test vectors (no real secrets)
REDACTION_TEST_VECTORS: tuple[dict[str, str], ...] = (
    {"input": "host 192.168.1.42 ping", "expect_category": "ipv4"},
    {"input": "mac aa:bb:cc:dd:ee:ff seen", "expect_category": "mac_address"},
    {"input": "contact user@example.com", "expect_category": "email"},
    {"input": "path /home/volker/data", "expect_category": "user_home_path"},
    {"input": "token ghp_abcdefghijklmnopqrstuvwxyz1234567890", "expect_category": "api_token"},
)


def redact_text(text: str, *, categories: tuple[str, ...] | None = None) -> RedactionResult:
    """Apply public-safe redaction patterns (local preview only)."""
    active = categories or REDACTION_CATEGORIES
    matched: list[str] = []
    out = text
    for cat in active:
        pat = _PATTERNS.get(cat)
        if not pat:
            continue
        if pat.search(out):
            matched.append(cat)
            out = pat.sub(_PLACEHOLDER, out)
    return RedactionResult(
        original_length=len(text),
        redacted_text=out,
        categories_matched=tuple(matched),
    )


def validate_test_vectors(
    *,
    redact_fn: Callable[[str], RedactionResult] = redact_text,
) -> list[str]:
    """Return list of failing vector labels (empty = all pass)."""
    failures: list[str] = []
    for i, vec in enumerate(REDACTION_TEST_VECTORS):
        result = redact_fn(vec["input"])
        cat = vec["expect_category"]
        if cat not in result.categories_matched:
            failures.append(f"vector_{i}:{cat}")
        if vec["input"] == result.redacted_text:
            failures.append(f"vector_{i}:not_redacted")
    return failures
