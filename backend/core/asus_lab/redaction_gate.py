"""Secret redaction gate for ASUS lab evidence import."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("bitlocker_recovery_key", re.compile(r"\b(?:[0-9]{6}-){7}[0-9]{6}\b")),
    ("wifi_psk", re.compile(r"(?i)(psk|wifi.?password|wpa.?passphrase)\s*[:=]\s*\S+")),
    ("api_token", re.compile(r"(?i)(api[_-]?token|bearer|authorization)\s*[:=]\s*\S+")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")),
    ("ssh_key_blob", re.compile(r"(?i)ssh-(?:rsa|ed25519)\s+[A-Za-z0-9+/=]{40,}")),
)


def scan_text(text: str) -> dict[str, Any]:
    hits: list[str] = []
    for name, pattern in _PATTERNS:
        if pattern.search(text or ""):
            hits.append(name)
    if hits:
        status = "blocked" if "private_key" in hits or "bitlocker_recovery_key" in hits else "redacted"
    else:
        status = "clean"
    return {"schema_version": SCHEMA_VERSION, "status": status, "hits": hits}


def redact_text(text: str) -> str:
    out = text or ""
    for name, pattern in _PATTERNS:
        out = pattern.sub(f"[redacted:{name}]", out)
    return out


def evaluate_path(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": SCHEMA_VERSION, "status": "clean", "hits": [], "path": str(path)}
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "quarantined",
            "hits": ["read_error"],
            "error": str(exc)[:200],
            "path": str(path),
        }
    # Skip obvious binaries
    if b"\0" in raw[:2048]:
        return {"schema_version": SCHEMA_VERSION, "status": "clean", "hits": [], "path": str(path), "binary": True}
    text = raw.decode("utf-8", errors="replace")
    result = scan_text(text)
    result["path"] = str(path)
    if result["status"] == "redacted":
        redacted = path.with_suffix(path.suffix + ".redacted")
        redacted.write_text(redact_text(text), encoding="utf-8")
        result["redacted_path"] = str(redacted)
    return result


def evaluate_tree(root: Path) -> dict[str, Any]:
    statuses: list[str] = []
    details: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith(".redacted"):
            continue
        item = evaluate_path(path)
        details.append(item)
        statuses.append(str(item.get("status")))
    if "blocked" in statuses:
        overall = "blocked"
    elif "quarantined" in statuses:
        overall = "quarantined"
    elif "redacted" in statuses:
        overall = "redacted"
    else:
        overall = "clean"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": overall,
        "files_scanned": len(details),
        "details": details,
        "import_allowed": overall in {"clean", "redacted"},
    }
