"""Rescue evidence/log spool — FAT32 ESP paths with /run fallback."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SPOOL_ROOT_REL = "setuphelfer/evidence"
LOG_ROOT_REL = "setuphelfer/logs"
STATE_REL = "setuphelfer/state/rescue-state.json"
PROFILE_ROOT_REL = "setuphelfer/profiles/machines"

ALLOWED_EVENT_CATEGORIES: tuple[str, ...] = (
    "boot",
    "medium-check",
    "network",
    "telemetry",
    "ui",
    "hardware",
)

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(password|passwd|psk|secret|token|api[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)wpa-psk"),
    re.compile(r"(?i)bearer\s+[a-z0-9._-]+", re.I),
)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def sanitize_rescue_log(text: str) -> str:
    """Redact likely secrets from log/evidence text."""
    out = text or ""
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def resolve_spool_base(
    *,
    esp_mount: Path | None = None,
    run_fallback: Path | None = None,
) -> Path:
    esp = esp_mount or Path("/media/SETUPHELFER")
    if (esp / SPOOL_ROOT_REL).exists() or esp.is_dir():
        try:
            test = esp / SPOOL_ROOT_REL
            test.parent.mkdir(parents=True, exist_ok=True)
            return esp
        except OSError:
            pass
    return run_fallback or Path("/run/setuphelfer")


def evidence_category_path(base: Path, category: str) -> Path:
    if category not in ALLOWED_EVENT_CATEGORIES:
        raise ValueError(f"unsupported evidence category: {category}")
    return base / SPOOL_ROOT_REL / category


def write_rescue_evidence_event(
    event: Mapping[str, Any],
    *,
    base: Path,
    category: str = "boot",
    best_effort: bool = True,
) -> dict[str, Any]:
    """Append one JSONL evidence event. Never raises when best_effort=True."""
    sanitized = dict(event)
    if "message" in sanitized and isinstance(sanitized["message"], str):
        sanitized["message"] = sanitize_rescue_log(sanitized["message"])
    sanitized.setdefault("recorded_at", _now_iso())
    sanitized.setdefault("category", category)
    sanitized["secrets_exposed"] = False

    dest_dir = evidence_category_path(base, category)
    dest = dest_dir / "events.jsonl"
    result = {
        "written": False,
        "path": str(dest),
        "category": category,
        "best_effort": best_effort,
        "error": None,
    }
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        line = json.dumps(sanitized, ensure_ascii=False) + "\n"
        with dest.open("a", encoding="utf-8") as fh:
            fh.write(line)
        result["written"] = True
    except OSError as exc:
        result["error"] = str(exc)
        if not best_effort:
            raise
    return result


def build_spool_layout_manifest(base: Path | None = None) -> dict[str, Any]:
    root = base or Path("/media/SETUPHELFER")
    paths = [f"{SPOOL_ROOT_REL}/{c}" for c in ALLOWED_EVENT_CATEGORIES]
    paths.extend([f"{LOG_ROOT_REL}/boot", f"{LOG_ROOT_REL}/journal", STATE_REL, PROFILE_ROOT_REL])
    return {
        "schema_version": 1,
        "base": str(root),
        "paths": paths,
        "fallback": "/run/setuphelfer/evidence",
        "secrets_exposed": False,
    }
