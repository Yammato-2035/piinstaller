#!/usr/bin/env python3
"""
Backup-Evidence-Collector: sammelt Diagnose-Artefakte pro job_id ohne harten Fehler.

Schreibt nach (Priorität):
  /var/lib/setuphelfer/evidence/backup-jobs/<job_id>/
  sonst /tmp/setuphelfer-evidence-<job_id>/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _run_capture(
    label: str,
    cmd: list[str],
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    rec: dict[str, Any] = {"label": label, "cmd": cmd, "ok": False, "permission_denied": False, "stderr_excerpt": ""}
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        rec["returncode"] = cp.returncode
        rec["stdout"] = (cp.stdout or "")[:200_000]
        rec["ok"] = cp.returncode == 0
        err = (cp.stderr or "").strip()
        rec["stderr_excerpt"] = err[:2000]
        if "Permission denied" in err or "Zugriff verweigert" in err:
            rec["permission_denied"] = True
    except subprocess.TimeoutExpired:
        rec["error"] = "timeout"
    except FileNotFoundError:
        rec["error"] = "binary_not_found"
    except PermissionError:
        rec["permission_denied"] = True
        rec["error"] = "permission_denied"
    except OSError as e:
        rec["error"] = str(e)
    return rec


def collect_backup_job_evidence(
    job_id: str,
    *,
    status_dir: Path,
    unit_name: str,
    unit_scope: str = "system",
    backup_dir: str | None = None,
) -> dict[str, Any]:
    job_id = job_id.strip()
    primary = Path("/var/lib/setuphelfer/evidence/backup-jobs") / job_id
    out_dir = primary
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        probe = out_dir / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError:
        out_dir = Path(f"/tmp/setuphelfer-evidence-{job_id}")
        out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "schema": "setuphelfer.backup_evidence.v1",
        "job_id": job_id,
        "collected_at": _now_iso(),
        "output_dir": str(out_dir),
        "artifacts": [],
        "permission_denied": [],
    }

    def _copy_if_exists(src: Path, dest_name: str) -> None:
        if not src.is_file():
            manifest["artifacts"].append({"name": dest_name, "status": "missing", "path": str(src)})
            return
        try:
            dst = out_dir / dest_name
            dst.write_bytes(src.read_bytes())
            manifest["artifacts"].append({"name": dest_name, "status": "copied", "bytes": dst.stat().st_size})
        except OSError as e:
            manifest["artifacts"].append({"name": dest_name, "status": "error", "detail": str(e)})

    status_file = status_dir / job_id / "status.json"
    job_file = status_dir / job_id / "job.json"
    _copy_if_exists(status_file, "status.json")
    _copy_if_exists(job_file, "job.json")

    log_path = Path("/var/log/setuphelfer") / f"backup-{job_id}.log"
    _copy_if_exists(log_path, f"backup-{job_id}.log")

    un = unit_name.strip() or f"setuphelfer-backup@{job_id}.service"
    manifest["captures"] = []
    cap_specs: list[tuple[str, list[str]]] = [
        ("systemctl_status", ["systemctl", "status", un, "--no-pager"]),
        (
            "systemctl_show",
            [
                "systemctl",
                "show",
                un,
                "-p",
                "TimeoutStartUSec",
                "-p",
                "TimeoutStopUSec",
                "-p",
                "RuntimeMaxUSec",
                "-p",
                "FragmentPath",
                "-p",
                "DropInPaths",
            ],
        ),
        ("journal_unit_tail", ["journalctl", "-u", un, "-n", "200", "--no-pager"]),
        ("journal_kernel_tail", ["journalctl", "-k", "-n", "120", "--no-pager"]),
        ("dmesg_tail", ["dmesg", "-T"]),
    ]
    if backup_dir:
        bd = backup_dir.strip()
        cap_specs.extend(
            [
                ("findmnt", ["findmnt", "-T", bd]),
                ("lsblk", ["lsblk", "-f"]),
                ("df", ["df", "-h", bd]),
            ]
        )

    for label, cmd in cap_specs:
        rec = _run_capture(label, cmd)
        manifest["captures"].append(rec)
        fn = f"capture_{label}.txt"
        try:
            body = ""
            if rec.get("ok") and isinstance(rec.get("stdout"), str):
                body = rec["stdout"]
            else:
                body = json.dumps(rec, ensure_ascii=False, indent=2)
            (out_dir / fn).write_text(body[:500_000], encoding="utf-8", errors="replace")
            manifest["artifacts"].append({"name": fn, "status": "written"})
        except OSError as e:
            manifest["artifacts"].append({"name": fn, "status": "error", "detail": str(e)})

    opt_runner = Path("/opt/setuphelfer/backend/tools/backup_runner.py")
    opt_app = Path("/opt/setuphelfer/backend/app.py")
    for label, pth in (("sha256_backup_runner.py", opt_runner), ("sha256_app.py", opt_app)):
        digest = _sha256_file(pth)
        manifest["artifacts"].append({"name": label, "path": str(pth), "sha256": digest, "status": "digest_only"})

    for c in manifest["captures"]:
        if c.get("permission_denied"):
            manifest["permission_denied"].append(c.get("label"))

    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    p = argparse.ArgumentParser(description="Setuphelfer backup evidence collector")
    p.add_argument("--job-id", required=True)
    p.add_argument("--status-dir", default="/var/lib/setuphelfer/backup-jobs")
    p.add_argument("--unit-name", default="")
    p.add_argument("--unit-scope", default="system")
    p.add_argument("--backup-dir", default="")
    args = p.parse_args()
    sd = Path(args.status_dir).resolve()
    un = args.unit_name.strip() or f"setuphelfer-backup@{args.job_id.strip()}.service"
    m = collect_backup_job_evidence(
        args.job_id,
        status_dir=sd,
        unit_name=un,
        unit_scope=args.unit_scope.strip() or "system",
        backup_dir=args.backup_dir.strip() or None,
    )
    print(json.dumps({"status": "ok", "output_dir": m.get("output_dir")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
