"""Import physical E2E evidence from SETUP_LOGS into workspace docs."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_EVIDENCE_FILES = frozenset(
    {
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
    }
)

_REDACT_PATTERNS = (
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "0.0.0.0"),
    (re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b"), "00:00:00:00:00:00"),
    (re.compile(r"(?i)(Bearer\s+\S+|Authorization:\s*\S+)"), "Bearer [redacted]"),
    (re.compile(r"(?i)(telemetry-lab-token|api[_-]?key\s*[=:]\s*\S+)"), "[redacted]"),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def redact_text(text: str) -> str:
    out = text
    for pattern, repl in _REDACT_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def find_setup_logs_mount() -> Path | None:
    for pattern in ("/media/*/SETUP_LOGS", "/run/media/*/SETUP_LOGS", "/mnt/setup_logs"):
        for path in sorted(Path("/").glob(pattern.lstrip("/"))):
            if path.is_dir():
                return path
    for label in ("SETUP_LOGS", "SETUPHELFER_LOGS"):
        by_label = Path(f"/dev/disk/by-label/{label}")
        if not by_label.exists():
            continue
        for mount in Path("/proc/mounts").read_text(encoding="utf-8").splitlines():
            parts = mount.split()
            if len(parts) >= 2 and (parts[0].endswith(label) or label in parts[0]):
                return Path(parts[1])
    return None


def list_e2e_run_dirs(setup_logs_base: Path) -> list[Path]:
    root = setup_logs_base / "setuphelfer" / "evidence" / "e2e"
    if not root.is_dir():
        return []
    return sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)


def import_e2e_run_evidence(
    run_dir: Path,
    *,
    repo_root: Path,
    setup_logs_base: Path | None = None,
) -> dict[str, Any]:
    if not run_dir.is_dir():
        raise ValueError("run_dir_missing")

    run_id = run_dir.name
    dest = repo_root / "docs" / "evidence" / "e2e_live_001d" / "physical_run" / run_id
    dest.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    missing_required: list[str] = []
    required = {
        "event-journal.jsonl",
        "e2e-result.json",
        "backup-result.json",
        "verify-result.json",
        "restore-result.json",
        "manifest-comparison.json",
    }

    for name in ALLOWED_EVIDENCE_FILES:
        src = run_dir / name
        if not src.is_file():
            if name in required:
                missing_required.append(name)
            continue
        raw = src.read_text(encoding="utf-8", errors="replace")
        clean = redact_text(raw)
        (dest / name).write_text(clean, encoding="utf-8")
        copied.append(name)

    manifest = {
        "schema_version": 1,
        "feature": "SETUPHELFER-E2E-LIVE-001D",
        "imported_at": _utc_now(),
        "physical_e2e_run_id": run_id,
        "source_run_dir": str(run_dir),
        "setup_logs_base": str(setup_logs_base or ""),
        "files_copied": copied,
        "missing_required": missing_required,
        "import_ok": not missing_required,
        "destination": str(dest),
    }
    (dest / "import-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    latest_link = repo_root / "docs" / "evidence" / "e2e_live_001d" / "physical_run_latest.json"
    latest_link.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def import_latest_e2e_evidence(*, repo_root: Path, setup_logs_base: Path | None = None) -> dict[str, Any]:
    base = setup_logs_base or find_setup_logs_mount()
    if base is None:
        return {"import_ok": False, "error": "setup_logs_not_mounted"}
    runs = list_e2e_run_dirs(base)
    if not runs:
        return {"import_ok": False, "error": "no_e2e_runs_found", "setup_logs_base": str(base)}
    return import_e2e_run_evidence(runs[0], repo_root=repo_root, setup_logs_base=base)
