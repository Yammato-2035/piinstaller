"""Phase A — evaluate physical E2E evidence after MSI Lab boot (001D5)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUCCESS_STATUSES = frozenset(
    {
        "passed",
        "ok",
        "success",
        "completed",
        "physical_rescue_backup_restore_e2e_passed",
        "physical_rescue_telemetry_diagnostics_e2e_passed",
        "physical_rescue_passed_server_verification_pending",
    }
)


def _parse_iso(value: str | None) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _result_mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _is_success_payload(data: dict[str, Any]) -> bool:
    status = str(data.get("status") or data.get("result") or data.get("terminal_status") or "").lower()
    if status in SUCCESS_STATUSES:
        return True
    if data.get("ok") is True:
        return True
    if data.get("physical_backup_restore_passed") is True:
        return True
    return False


def evaluate_phase_a_physical_e2e(setup_logs_base: Path) -> dict[str, Any]:
    """Require evidence newer than the armed physical run-control (ignore older lab runs)."""
    logs = Path(setup_logs_base)
    control_path = logs / "setuphelfer/e2e-live-001d/run-control.json"
    ctrl: dict[str, Any] = {}
    if control_path.is_file():
        try:
            loaded = json.loads(control_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                ctrl = loaded
        except json.JSONDecodeError:
            ctrl = {}

    e2e_root = logs / "setuphelfer" / "evidence" / "e2e"
    candidates: list[Path] = []
    if e2e_root.is_dir():
        candidates.extend(e2e_root.glob("**/auto-physical-e2e-result.json"))
        candidates.extend(e2e_root.glob("**/e2e-result.json"))
    candidates = sorted(set(candidates), key=lambda p: p.stat().st_mtime, reverse=True)

    created = _parse_iso(str(ctrl.get("created_at") or ""))
    # Prefer results written after this arming; allow 60s clock skew.
    min_mtime = None
    if created is not None:
        min_mtime = created.timestamp() - 60

    fresh: list[Path] = []
    for path in candidates:
        if min_mtime is None or path.stat().st_mtime >= min_mtime:
            fresh.append(path)

    out: dict[str, Any] = {
        "setup_logs": str(logs),
        "run_control_path": str(control_path) if control_path.is_file() else None,
        "run_control_enabled": bool(ctrl.get("enabled")),
        "run_control_consumed": bool(ctrl.get("consumed")),
        "run_control_terminal": ctrl.get("terminal_status"),
        "run_nonce": ctrl.get("run_nonce"),
        "armed_at": ctrl.get("created_at"),
        "result_files_all": [str(p) for p in candidates[:8]],
        "result_files_fresh": [str(p) for p in fresh[:5]],
        "production_ready": False,
    }

    if not ctrl:
        out.update({"ok": False, "code": "phase_a_run_control_missing", "message": "Kein Physical-E2E-Run-Control."})
        return out

    if not fresh:
        out.update(
            {
                "ok": False,
                "code": "phase_a_pending_msi_boot",
                "message": (
                    "Kein frisches Physical-E2E-Ergebnis seit Armierung — "
                    "MSI mit Lab-Auto Physical E2E booten (SABRENT angeschlossen)."
                ),
            }
        )
        return out

    # Prefer the run recorded on run-control (a later blocked reboot must not hide success).
    consumed_run = str(ctrl.get("consumed_by_run_id") or "").strip()
    terminal = str(ctrl.get("terminal_status") or "").strip()
    if terminal.lower() in SUCCESS_STATUSES or terminal in SUCCESS_STATUSES:
        preferred: list[Path] = []
        if consumed_run:
            preferred = [p for p in fresh if consumed_run in str(p)]
        chosen = preferred[0] if preferred else None
        if chosen is None:
            for path in fresh:
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if isinstance(payload, dict) and _is_success_payload(payload):
                    chosen = path
                    break
        if chosen is not None:
            try:
                data = json.loads(chosen.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {"status": terminal}
            if not isinstance(data, dict):
                data = {"status": terminal}
            out.update(
                {
                    "ok": True,
                    "code": "phase_a_passed",
                    "latest_result": str(chosen),
                    "latest_mtime": _result_mtime(chosen).isoformat().replace("+00:00", "Z"),
                    "status": str(data.get("status") or terminal),
                    "summary": {
                        k: data.get(k)
                        for k in ("status", "result", "phases", "backup", "verify", "restore", "errors", "integrity")
                        if k in data
                    }
                    or {"status": terminal, "consumed_by_run_id": consumed_run},
                }
            )
            return out

    # Otherwise pick newest success among fresh results; skip blocked one-shots.
    latest = fresh[0]
    for path in fresh:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and _is_success_payload(payload):
            latest = path
            break

    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        out.update({"ok": False, "code": "phase_a_result_invalid_json", "latest_result": str(latest)})
        return out
    if not isinstance(data, dict):
        out.update({"ok": False, "code": "phase_a_result_not_object", "latest_result": str(latest)})
        return out

    status = str(data.get("status") or data.get("result") or data.get("terminal_status") or "")
    passed = _is_success_payload(data)
    out.update(
        {
            "ok": passed,
            "code": "phase_a_passed" if passed else "phase_a_failed",
            "latest_result": str(latest),
            "latest_mtime": _result_mtime(latest).isoformat().replace("+00:00", "Z"),
            "status": status,
            "summary": {
                k: data.get(k)
                for k in ("status", "result", "phases", "backup", "verify", "restore", "errors", "integrity")
                if k in data
            },
        }
    )
    return out
