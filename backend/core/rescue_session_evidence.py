"""PI-RS-MSI-GUI-003 — per-boot session evidence isolation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SESSION_SCHEMA_VERSION = 1

_SESSION_ROOT = Path("/run/setuphelfer/sessions")
_CURRENT_SESSION_LINK = Path("/run/setuphelfer/current-session.json")
_BOOT_EVIDENCE_FILES = (
    "gui-availability.json",
    "gui-fallback.json",
    "rescue-ui-status.json",
    "gui-start.log",
    "boot-timeline.jsonl",
    "console-shield.json",
    "console-ownership.json",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def session_root() -> Path:
    return _SESSION_ROOT


def current_session_pointer_path() -> Path:
    return _CURRENT_SESSION_LINK


def build_session_meta(
    *,
    session_id: str,
    boot_id: str,
    payload_version: str,
    session_started_at: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SESSION_SCHEMA_VERSION,
        "session_id": session_id,
        "boot_id": boot_id,
        "payload_version": payload_version,
        "session_started_at": session_started_at or _utc_now(),
        "current_session_evidence": True,
        "stale_evidence_detected": False,
    }


def init_boot_session(
    *,
    session_id: str,
    boot_id: str,
    payload_version: str,
    session_started_at: str | None = None,
    root: Path | None = None,
    pointer_path: Path | None = None,
) -> dict[str, Any]:
    meta = build_session_meta(
        session_id=session_id,
        boot_id=boot_id,
        payload_version=payload_version,
        session_started_at=session_started_at,
    )
    base = (root or session_root()) / session_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "session-meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pointer = pointer_path or current_session_pointer_path()
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for name in _BOOT_EVIDENCE_FILES:
        placeholder = base / name
        if name.endswith(".jsonl") or name.endswith(".log"):
            placeholder.write_text("", encoding="utf-8")
        else:
            placeholder.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "session_id": session_id,
                        "boot_id": boot_id,
                        "payload_version": payload_version,
                        "session_started_at": meta["session_started_at"],
                        "initialized": True,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
    return meta


def load_current_session_meta(path: Path | None = None) -> dict[str, Any] | None:
    target = path or current_session_pointer_path()
    if not target.is_file():
        return None
    data = json.loads(target.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def evaluate_evidence_freshness(
    evidence: dict[str, Any],
    *,
    current_session: dict[str, Any],
) -> dict[str, Any]:
    current_id = str(current_session.get("session_id") or "")
    current_boot = str(current_session.get("boot_id") or "")
    current_started = str(current_session.get("session_started_at") or "")
    current_payload = str(current_session.get("payload_version") or "")

    evidence_session = str(evidence.get("session_id") or evidence.get("SESSION_ID") or "")
    evidence_boot = str(evidence.get("boot_id") or evidence.get("BOOT_ID") or "")
    evidence_started = str(evidence.get("session_started_at") or evidence.get("timestamp") or "")
    evidence_payload = str(evidence.get("payload_version") or "")

    stale_reasons: list[str] = []
    if evidence_session and evidence_session != current_id:
        stale_reasons.append("session_id_mismatch")
    if evidence_boot and evidence_boot != current_boot:
        stale_reasons.append("boot_id_mismatch")
    if evidence_payload and evidence_payload != current_payload:
        stale_reasons.append("payload_version_mismatch")
    if evidence_started and current_started and evidence_started < current_started:
        stale_reasons.append("timestamp_before_session_start")

    stale = bool(stale_reasons)
    return {
        "current_session_evidence": not stale,
        "stale_evidence_detected": stale,
        "stale_reasons": stale_reasons,
        "session_id": evidence_session or None,
        "boot_id": evidence_boot or None,
    }


def annotate_evidence_document(document: dict[str, Any], session_meta: dict[str, Any]) -> dict[str, Any]:
    merged = dict(document)
    merged["session_id"] = session_meta.get("session_id")
    merged["boot_id"] = session_meta.get("boot_id")
    merged["payload_version"] = session_meta.get("payload_version")
    merged["session_started_at"] = session_meta.get("session_started_at")
    return merged
