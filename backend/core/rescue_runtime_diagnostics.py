"""
Rescue runtime diagnostics collector — read-only discovery with redacted output.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_backup_plan_contract import build_rescue_backup_plan
from core.rescue_setup_logs_persistence import resolve_rescue_evidence_root
from core.rescue_wifi_diagnostics import classify_wifi_status
from core.telemetry_redaction_contract import redact_telemetry_payload

DIAGNOSTICS_VERSION = 1

_LOCAL_EVIDENCE = Path("/var/lib/setuphelfer-rescue/local/evidence")
_RUN_EVIDENCE = Path("/run/setuphelfer/evidence")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run_text(cmd: list[str], *, timeout: int = 12) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=timeout)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return f"[unavailable:{type(exc).__name__}]"


def collect_rescue_runtime_diagnostics(*, plan_dry_run: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence = resolve_rescue_evidence_root()
    wifi = classify_wifi_status()
    payload: dict[str, Any] = {
        "schema_version": DIAGNOSTICS_VERSION,
        "collected_at": _utc_now(),
        "date": _run_text(["date", "-u"]),
        "uname": _run_text(["uname", "-a"]).strip(),
        "os_release": _run_text(["cat", "/etc/os-release"]).strip(),
        "lsblk_json": _run_text(["lsblk", "-J", "-o", "NAME,PATH,TYPE,SIZE,MODEL,SERIAL,TRAN,FSTYPE,FSVER,LABEL,UUID,PARTUUID,MOUNTPOINTS,ROTA,RM,HOTPLUG"]),
        "blkid": _run_text(["blkid"]).strip(),
        "findmnt_json": _run_text(["findmnt", "-J"]),
        "ip_link": _run_text(["ip", "link"]).strip(),
        "ip_addr": _run_text(["ip", "addr"]).strip(),
        "rfkill": _run_text(["rfkill", "list"]).strip(),
        "nmcli_device": _run_text(["nmcli", "device", "status"]).strip(),
        "nmcli_radio": _run_text(["nmcli", "radio", "all"]).strip(),
        "nmcli_wifi_list": _run_text(["nmcli", "device", "wifi", "list"]),
        "iw_dev": _run_text(["iw", "dev"]).strip(),
        "lspci": _run_text(["lspci", "-nnk"]).strip(),
        "lsusb": _run_text(["lsusb"]).strip(),
        "dmesg_network": _run_text(["dmesg", "--ctime"]).strip()[-8000:],
        "networkmanager_status": _run_text(["systemctl", "status", "NetworkManager", "--no-pager"]),
        "backend_service_status": _run_text(["systemctl", "status", "setuphelfer-backend.service", "--no-pager"]),
        "wifi_diagnostics": wifi,
        "evidence": evidence,
        "network_upload_attempted": False,
    }
    if plan_dry_run:
        payload["backup_plan_dry_run"] = build_rescue_backup_plan(plan_dry_run)
    return payload


def write_rescue_runtime_diagnostics(
    *,
    plan_dry_run: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw = collect_rescue_runtime_diagnostics(plan_dry_run=plan_dry_run)
    redacted = redact_telemetry_payload(raw)
    evidence = resolve_rescue_evidence_root()
    if evidence.get("persistent"):
        out_dir = Path(str(evidence["evidence_root"]))
        non_persistent = False
        warning = None
    else:
        out_dir = Path(str(evidence.get("evidence_root") or _RUN_EVIDENCE))
        non_persistent = True
        warning = evidence.get("warning") or "Evidence ist nicht persistent, bitte SETUP_LOGS prüfen"
        try:
            _RUN_EVIDENCE.mkdir(parents=True, exist_ok=True)
            _LOCAL_EVIDENCE.mkdir(parents=True, exist_ok=True)
            for name, body in (
                ("rescue_runtime_diagnostics.json", raw),
                ("rescue_runtime_diagnostics_redacted.json", redacted),
            ):
                (_LOCAL_EVIDENCE / name).write_text(
                    json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
        except OSError:
            pass

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / "rescue_runtime_diagnostics.json",
        "redacted": out_dir / "rescue_runtime_diagnostics_redacted.json",
        "log": out_dir / "rescue_runtime_diagnostics.log",
    }
    paths["json"].write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["redacted"].write_text(json.dumps(redacted, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log_lines = [
        f"collected_at={raw.get('collected_at')}",
        f"persistent={not non_persistent}",
        f"evidence_root={out_dir}",
        f"wifi_status={raw.get('wifi_diagnostics', {}).get('status')}",
    ]
    if warning:
        log_lines.append(f"warning={warning}")
    paths["log"].write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    return {
        "status": "ok",
        "paths": {k: str(v) for k, v in paths.items()},
        "persistent": not non_persistent,
        "non_persistent": non_persistent,
        "warning": warning,
        "network_upload_attempted": False,
    }
