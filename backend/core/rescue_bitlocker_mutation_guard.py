"""BitLocker mutation hard-block (PI-RS-ASUS-LAB-CONTROL-006).

Read-only status inspection is allowed. No keys in logs.
"""

from __future__ import annotations

import re
from typing import Any

SCHEMA_VERSION = 1

# Patterns that must never execute in lab shell / remote jobs.
BITLOCKER_MUTATION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\bmanage-bde\b.*\s(-on|-off|-pause|-resume|-protectors\s+-add|-protectors\s+-delete|-lock|-unlock)\b",
        r"\bEnable-BitLocker\b",
        r"\bDisable-BitLocker\b",
        r"\bSuspend-BitLocker\b",
        r"\bResume-BitLocker\b",
        r"\bAdd-BitLockerKeyProtector\b",
        r"\bRemove-BitLockerKeyProtector\b",
        r"\bClear-BitLockerAutoUnlock\b",
        r"\bBackup-BitLockerKeyProtector\b",
        r"\breagentc\b.*\/disable",
        r"bitlocker_mutation\s*[:=]\s*true",
    )
)

RECOVERY_KEY_RE = re.compile(
    r"\b(?:[0-9]{6}-){7}[0-9]{6}\b|\bRecovery\s*Key\s*[:=]\s*\S+",
    re.I,
)


def is_bitlocker_mutation_command(command: str) -> bool:
    text = command or ""
    return any(p.search(text) for p in BITLOCKER_MUTATION_PATTERNS)


def redact_bitlocker_secrets(text: str) -> str:
    return RECOVERY_KEY_RE.sub("[redacted-bitlocker-secret]", text or "")


def evaluate_bitlocker_command_gate(command: str) -> dict[str, Any]:
    blocked = is_bitlocker_mutation_command(command)
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": not blocked,
        "bitlocker_mutation": False,
        "blocked": blocked,
        "blocked_reason": "bitlocker_mutation_forbidden" if blocked else None,
        "command_redacted": redact_bitlocker_secrets(command)[:2000],
    }
