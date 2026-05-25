"""
Kontrollierter Deploy-Orchestrator fuer das Development Dashboard.

Der unprivilegierte Backend-Prozess startet niemals direkt deploy-to-opt.sh,
sondern hoechstens die vordefinierte systemd-Oneshot-Unit.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.deploy_job_state import (
    DEFAULT_SYSTEMD_UNIT,
    build_deploy_job_state,
    get_deploy_state_paths,
    read_deploy_job_log_tail,
    redact_deploy_log_text,
)

SYSTEMD_UNIT_SOURCE = "packaging/systemd/setuphelfer-deploy-helper.service"
ROOT_HELPER_SOURCE = "scripts/setuphelfer-deploy-helper-root.sh"
ROOT_HELPER_TARGET = "/opt/setuphelfer/scripts/setuphelfer-deploy-helper-root.sh"
SYSTEMD_UNIT_TARGET_DIR = "/etc/systemd/system"
SUDOERS_EXAMPLE = "packaging/sudoers.d/setuphelfer-deploy-helper.example"
REQUEST_TIMEOUT_SEC = 15

_PERMISSION_DENIED_TOKENS = (
    "permission denied",
    "access denied",
    "interactive authentication required",
    "authentication is required",
    "not authorized",
)


def _state_with_code(payload: dict[str, Any]) -> dict[str, Any]:
    return {"code": deploy_status_api_code(payload), **payload}


def deploy_status_api_code(payload: dict[str, Any]) -> str:
    status = str(payload.get("status") or "unknown").lower()
    next_action = str(((payload.get("next_action") or {}).get("type")) or "none").lower()
    if status == "success":
        return "DEV_DASHBOARD_DEPLOY_SUCCESS"
    if status == "failed":
        return "DEV_DASHBOARD_DEPLOY_FAILED"
    if status == "operator_required":
        return "DEV_DASHBOARD_DEPLOY_OPERATOR_REQUIRED"
    if status == "blocked":
        return "DEV_DASHBOARD_DEPLOY_BLOCKED"
    if status == "running":
        return "DEV_DASHBOARD_DEPLOY_REQUEST_ACCEPTED"
    if next_action == "deploy_required":
        return "DEV_DASHBOARD_DEPLOY_REQUIRED"
    return "DEV_DASHBOARD_DEPLOY_STATUS_OK"


def get_deploy_status() -> dict[str, Any]:
    return _state_with_code(build_deploy_job_state())


def build_deploy_operator_setup_commands() -> dict[str, Any]:
    workspace = str(get_deploy_state_paths()["workspace"])
    commands = [
        f"sudo cp {SYSTEMD_UNIT_SOURCE} {SYSTEMD_UNIT_TARGET_DIR}/",
        f"sudo cp {ROOT_HELPER_SOURCE} {ROOT_HELPER_TARGET}",
        f"sudo chmod 0755 {ROOT_HELPER_TARGET}",
        "sudo systemctl daemon-reload",
        f"sudo systemctl status {DEFAULT_SYSTEMD_UNIT}",
    ]
    warnings = [
        "Nur Beispiel-Setup fuer den eng begrenzten Deploy-Helper.",
        "Kein NOPASSWD fuer deploy-to-opt.sh direkt.",
        f"Sudoers-Beispiel nur manuell pruefen: {SUDOERS_EXAMPLE}",
        f"Workspace bleibt fest auf {workspace}.",
    ]
    return {
        "status": "operator_required",
        "workspace": workspace,
        "systemd_unit": DEFAULT_SYSTEMD_UNIT,
        "commands": commands,
        "warnings": warnings,
    }


def _permission_denied(text: str) -> bool:
    low = (text or "").lower()
    return any(token in low for token in _PERMISSION_DENIED_TOKENS)


def request_controlled_deploy(operator_confirm: bool) -> dict[str, Any]:
    current = build_deploy_job_state()
    if not operator_confirm:
        return _state_with_code(
            {
                **current,
                "status": "blocked",
                "review_required": True,
                "errors": ["operator_confirm_required"],
                "message": "Kontrollierter Deploy nur nach ausdruecklicher Operator-Bestaetigung.",
            }
        )

    if int(current.get("workspace_dirty_count") or 0) > 0:
        return _state_with_code(
            {
                **current,
                "status": "blocked",
                "errors": ["workspace_dirty"],
                "message": "Workspace ist dirty; kontrollierter Deploy bleibt blockiert.",
            }
        )

    helper = dict(current.get("helper") or {})
    if not helper.get("systemd_unit_present"):
        setup = build_deploy_operator_setup_commands()
        return _state_with_code(
            {
                **current,
                "status": "operator_required",
                "errors": ["helper_unit_missing"],
                "message": "Deploy-Helper ist nicht installiert.",
                "helper": {
                    **helper,
                    "systemd_unit_present": False,
                    "can_start_without_password": "unknown",
                    "requires_operator_setup": True,
                },
                "operator_setup": setup,
            }
        )

    try:
        proc = subprocess.run(
            ["systemctl", "start", DEFAULT_SYSTEMD_UNIT],
            capture_output=True,
            text=True,
            timeout=REQUEST_TIMEOUT_SEC,
            check=False,
        )
        combined = redact_deploy_log_text(((proc.stdout or "") + "\n" + (proc.stderr or "")).strip())
    except subprocess.TimeoutExpired:
        latest = build_deploy_job_state()
        return _state_with_code(
            {
                **latest,
                "status": "running",
                "message": "Deploy-Helper wurde gestartet; Status ueber Dashboard-Logs weiter beobachten.",
            }
        )
    except OSError as exc:
        return _state_with_code(
            {
                **current,
                "status": "failed",
                "errors": [f"systemctl_start_failed:{exc}"],
                "message": "systemctl konnte nicht ausgefuehrt werden.",
            }
        )

    if proc.returncode == 0:
        latest = build_deploy_job_state()
        latest["message"] = "Deploy-Helper erfolgreich gestartet."
        return _state_with_code(latest)

    if _permission_denied(combined):
        setup = build_deploy_operator_setup_commands()
        return _state_with_code(
            {
                **current,
                "status": "operator_required",
                "errors": ["permission_denied"],
                "message": combined or "Start der systemd-Unit ist fuer den Backend-Prozess nicht freigeschaltet.",
                "helper": {
                    **helper,
                    "can_start_without_password": False,
                    "requires_operator_setup": True,
                },
                "operator_setup": setup,
            }
        )

    latest = build_deploy_job_state()
    return _state_with_code(
        {
            **latest,
            "status": "failed",
            "errors": [combined or f"systemctl_exit_{proc.returncode}"],
            "message": "Deploy-Helper konnte nicht gestartet werden.",
        }
    )


def read_deploy_logs() -> dict[str, Any]:
    state = build_deploy_job_state()
    paths = get_deploy_state_paths()
    return {
        "status": "success",
        "code": "DEV_DASHBOARD_DEPLOY_STATUS_OK",
        "log_file": str(paths["log_file"]),
        "lines": read_deploy_job_log_tail(max_lines=120),
        "last_job": state.get("last_job"),
    }
