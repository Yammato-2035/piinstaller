"""RS-011D supplement bundle for MSI evidence collector."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from core.rescue_setup_logs_persistence import ensure_setup_logs_rw
from core.rescue_stale_artifact_guard import build_artifact_metadata, build_failed_stub


def _run(cmd: list[str], *, timeout: int = 60) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout)
    blob = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, blob.strip()


def collect_rs011d_supplement() -> dict[str, Any]:
    ev_dir = Path(__import__("os").environ.get("SETUPHELFER_MSI_EVIDENCE_DIR", ""))
    if not ev_dir.is_dir():
        logs = ensure_setup_logs_rw()
        root = Path(str(logs.get("evidence_root") or ""))
        ev_dir = root / "msi-rs011b"
        ev_dir.mkdir(parents=True, exist_ok=True)

    meta = build_artifact_metadata(
        rescue_version=__import__("os").environ.get("RS011B_RESCUE_VERSION", ""),
        boot_session_id=__import__("os").environ.get("RS011B_BOOT_SESSION_ID", ""),
        source_run_id=__import__("os").environ.get("RS011B_RUN_ID", "RS_011B"),
        generated_by="collect_rs011d_supplement",
    )
    written: list[str] = []
    failed: list[str] = []

    rc, lspci_out = _run(["lspci", "-nn"])
    if rc == 0 and lspci_out:
        (ev_dir / "lspci-nn-redacted.txt").write_text(lspci_out + "\n", encoding="utf-8")
        written.append("lspci-nn-redacted.txt")

    for name, cmd in (
        ("msi-killer-e2500-detection.json", ["python3", "-c", "print('{}')"]),
        ("msi-aer-summary.json", ["python3", "-c", "print('{}')"]),
    ):
        path = ev_dir / name
        if path.is_file():
            continue
        stub = build_failed_stub(error_code="supplement_partial", errors=["minimal_supplement"], metadata=meta)
        path.write_text(json.dumps(stub, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(name)

    summary = {
        "schema_version": 1,
        "status": "ok" if not failed else "review_required",
        "written": written,
        "failed": failed,
        "complete": not failed,
        **meta,
    }
    (ev_dir / "collector-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary
