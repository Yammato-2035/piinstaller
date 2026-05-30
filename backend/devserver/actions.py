"""DevAction-Orchestrierung für read-only SSH."""

from __future__ import annotations

from typing import Any, Callable

from devserver.config import DevServerConfig
from devserver.models import default_dev_action, new_id, utc_now_iso
from devserver.ssh_readonly import (
    PROFILE_TO_ACTION_TYPE,
    parse_ssh_result_to_report,
    run_ssh_profile,
    validate_command_profile,
)
from devserver.storage import DevServerStorage

SshRunner = Callable[[list[str], int], dict[str, Any]]


def execute_ssh_profile_action(
    *,
    config: DevServerConfig,
    storage: DevServerStorage,
    node_id: str,
    profile_name: str,
    runner: SshRunner | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    if not config.enabled:
        return _blocked_response(errors=["dev_server_disabled"], warnings=warnings)

    if config.mode != "local_lab":
        return _blocked_response(errors=["not_local_lab_mode"], warnings=warnings)

    if not config.ssh_allowed:
        return _blocked_response(errors=["ssh_not_allowed"], warnings=warnings)

    if not validate_command_profile(profile_name):
        return _blocked_response(errors=["unknown_profile"], warnings=warnings)

    node = storage.load_node(node_id)
    if not node:
        return _blocked_response(errors=["node_not_found"], warnings=warnings)

    action_type = PROFILE_TO_ACTION_TYPE.get(profile_name, "ssh_check")
    from devserver.ssh_readonly import build_readonly_command_list

    commands = build_readonly_command_list(profile_name)
    action = default_dev_action(
        action_id=new_id("action"),
        node_id=node_id,
        action_type=action_type,
        command_profile=profile_name,
        commands=commands,
    )
    action["status"] = "running"
    action["started_at"] = utc_now_iso()
    node["status"] = "busy"
    node["current_action"] = action["action_id"]
    storage.save_node(node)
    storage.save_action(action)

    result = run_ssh_profile(node, profile_name, runner=runner)

    action["finished_at"] = utc_now_iso()
    action["stdout_excerpt"] = result.get("stdout") or ""
    action["stderr_excerpt"] = result.get("stderr") or ""
    action["exit_code"] = result.get("exit_code")

    report_id: str | None = None

    if result.get("blocked"):
        action["status"] = "blocked"
        errors.append(str(result.get("reason") or "blocked"))
        node["ssh"]["last_check_status"] = "not_configured" if profile_name == "ssh_check" else node["ssh"].get("last_check_status", "not_configured")
    elif result.get("ok"):
        action["status"] = "success"
        report = parse_ssh_result_to_report(node, profile_name, result)
        storage.save_report(report)
        report_id = report["report_id"]
        if profile_name == "ssh_check":
            node["ssh"]["last_check_status"] = "ok"
            node["ssh"]["last_check_error"] = ""
        node["status"] = "online"
    else:
        action["status"] = "failed"
        errors.append(str(result.get("reason") or "ssh_failed"))
        if profile_name == "ssh_check":
            node["ssh"]["last_check_status"] = "failed"
            node["ssh"]["last_check_error"] = action["stderr_excerpt"][:200]

    node["current_action"] = None
    storage.save_action(action)
    storage.save_node(node)

    storage.append_audit_event({
        "at": utc_now_iso(),
        "event_type": "ssh_action",
        "node_id": node_id,
        "action_id": action["action_id"],
        "profile": profile_name,
        "status": action["status"],
    })

    code = "DEV_SERVER_SSH_ACTION_SUCCESS"
    if action["status"] == "blocked":
        code = "DEV_SERVER_SSH_ACTION_BLOCKED"
    elif action["status"] == "failed":
        code = "DEV_SERVER_SSH_ACTION_FAILED"

    return {
        "code": code,
        "action": action,
        "report_id": report_id,
        "warnings": warnings,
        "errors": errors,
    }


def _blocked_response(*, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "code": "DEV_SERVER_SSH_ACTION_BLOCKED",
        "action": None,
        "report_id": None,
        "warnings": warnings,
        "errors": errors,
    }
