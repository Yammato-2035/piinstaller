#!/usr/bin/env python3
"""
Proof-of-contract runner for systemd-run backup jobs.

No real backup is executed in this POC.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _emit(event: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(event, ensure_ascii=True) + "\n")
    sys.stdout.flush()


class POCState:
    def __init__(self) -> None:
        self.cancel_requested = False


STATE = POCState()


def _on_sigterm(signum: int, frame: Any) -> None:
    STATE.cancel_requested = True
    _emit({"event": "signal", "signal": "SIGTERM", "ts": _now_iso()})


def _write_status(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Setuphelfer backup systemd-run POC runner")
    parser.add_argument("--job-id", required=True, help="Logical backup job id")
    parser.add_argument("--unit-name", default="", help="Systemd unit name (optional)")
    parser.add_argument("--state-dir", default="/var/lib/setuphelfer/backup-jobs", help="Base state directory")
    parser.add_argument("--simulate-seconds", type=int, default=6, help="Simulated runtime in seconds")
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, _on_sigterm)

    unit_name = args.unit_name.strip() or os.environ.get("SYSTEMD_UNIT", "").strip() or f"setuphelfer-backup-poc-{args.job_id}.service"
    job_dir = Path(args.state_dir).resolve() / args.job_id
    status_path = job_dir / "status.json"

    started = _now_iso()
    status = {
        "job_id": args.job_id,
        "unit_name": unit_name,
        "status": "running",
        "code": "backup.job.running",
        "severity": "info",
        "diagnosis_id": None,
        "backup_started_at": started,
        "backup_finished_at": None,
        "archive_path": None,
        "abort_reason": None,
        "progress_optional": 0,
    }
    _write_status(status_path, status)
    _emit({"event": "started", "job_id": args.job_id, "unit_name": unit_name, "ts": started})

    for i in range(max(args.simulate_seconds, 1)):
        if STATE.cancel_requested:
            finished = _now_iso()
            status.update(
                {
                    "status": "cancelled",
                    "code": "backup.cancelled",
                    "severity": "info",
                    "backup_finished_at": finished,
                    "abort_reason": "sigterm",
                    "progress_optional": int((i / max(args.simulate_seconds, 1)) * 100),
                }
            )
            _write_status(status_path, status)
            _emit({"event": "finished", "result": "cancelled", "job_id": args.job_id, "ts": finished})
            return 0
        pct = int(((i + 1) / max(args.simulate_seconds, 1)) * 100)
        status["progress_optional"] = pct
        _write_status(status_path, status)
        _emit({"event": "progress", "job_id": args.job_id, "progress": pct, "ts": _now_iso()})
        time.sleep(1)

    finished = _now_iso()
    status.update(
        {
            "status": "success",
            "code": "backup.success",
            "severity": "success",
            "backup_finished_at": finished,
            "abort_reason": None,
            "progress_optional": 100,
        }
    )
    _write_status(status_path, status)
    _emit({"event": "finished", "result": "success", "job_id": args.job_id, "ts": finished})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
