"""Local event journal on SETUP_LOGS for physical E2E runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

JOURNAL_FILES = (
    "event-journal.jsonl",
    "send-status.json",
    "receipts.json",
    "diagnostics-status.json",
    "backup-result.json",
    "verify-result.json",
    "restore-result.json",
    "source-summary.json",
    "backup-summary.json",
    "restored-summary.json",
    "manifest-comparison.json",
    "e2e-result.json",
    "operator-decisions.jsonl",
)

_FORBIDDEN_EVIDENCE_KEYS = frozenset(
    {
        "token",
        "authorization",
        "bearer",
        "secret",
        "private_key",
        "hmac",
        "signature",
        "api_key",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_evidence_base(setup_logs_mount: Path | None = None) -> Path:
    if setup_logs_mount is not None:
        return setup_logs_mount
    for cand in (
        Path("/run/setuphelfer/esp-rw"),
        Path("/mnt/setup_logs"),
    ):
        if (cand / "setuphelfer").is_dir() or cand.is_dir():
            return cand
    return Path("/run/setuphelfer/esp-rw")


def journal_dir_for_run(setup_logs_base: Path, e2e_run_id: str) -> Path:
    return setup_logs_base / "setuphelfer" / "evidence" / "e2e" / e2e_run_id


def ensure_journal_layout(journal_dir: Path) -> dict[str, str]:
    journal_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {"journal_dir": str(journal_dir)}
    for name in JOURNAL_FILES:
        target = journal_dir / name
        if name.endswith(".jsonl") and not target.exists():
            target.write_text("", encoding="utf-8")
        elif name.endswith(".json") and not target.exists():
            target.write_text("{}\n", encoding="utf-8")
        paths[name] = str(target)
    return paths


def _scrub_value(key: str, value: Any) -> Any:
    lowered = str(key).lower()
    if lowered in _FORBIDDEN_EVIDENCE_KEYS:
        return "[redacted]"
    if isinstance(value, dict):
        return {k: _scrub_value(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub_value(str(i), item) for i, item in enumerate(value)]
    return value


def scrub_evidence_record(record: dict[str, Any]) -> dict[str, Any]:
    return {k: _scrub_value(k, v) for k, v in record.items()}


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = scrub_evidence_record(record)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(clean, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = scrub_evidence_record(data)
    path.write_text(json.dumps(clean, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def append_event_journal(journal_dir: Path, event: dict[str, Any]) -> None:
    entry = {**event, "recorded_at": _utc_now()}
    append_jsonl(journal_dir / "event-journal.jsonl", entry)


def append_operator_decision(journal_dir: Path, decision: dict[str, Any]) -> None:
    entry = {**decision, "recorded_at": _utc_now()}
    append_jsonl(journal_dir / "operator-decisions.jsonl", entry)


def update_send_status(journal_dir: Path, status: dict[str, Any]) -> None:
    current = read_json(journal_dir / "send-status.json")
    current.update(status)
    current["updated_at"] = _utc_now()
    write_json(journal_dir / "send-status.json", current)


def store_receipt(journal_dir: Path, receipt: dict[str, Any]) -> None:
    current = read_json(journal_dir / "receipts.json")
    items = current.get("receipts")
    if not isinstance(items, list):
        items = []
    items.append(scrub_evidence_record({**receipt, "stored_at": _utc_now()}))
    write_json(journal_dir / "receipts.json", {"receipts": items, "count": len(items)})
