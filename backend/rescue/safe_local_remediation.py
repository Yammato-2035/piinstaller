"""
Allowlist-only safe local remediation engine.

PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007 Phase 8.

NEVER performs apt/dkms/nvidia proprietary/firmware flash/BIOS/
partition write/internal disk write/arbitrary shell. Actions are
planned and applied only when present in ``ALLOWED_ACTIONS``.
Execution is injected via an optional callable so unit tests stay
hardware-free.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

ALLOWED_ACTIONS: frozenset[str] = frozenset(
    {
        "retry_readonly_probe",
        "restart_setuphelfer_service",
        "kill_duplicate_setuphelfer_process",
        "remount_detect_only",
        "reinit_network",
        "clear_soft_rfkill",
        "activate_tui_fallback",
        "plan_next_boot_profile_params",
        "resolve_port_conflict_via_service_restart",
        "probe_load_reversible_kernel_module",
    }
)

FORBIDDEN_ACTION_PREFIXES: tuple[str, ...] = (
    "apt_",
    "dkms_",
    "nvidia_proprietary_",
    "firmware_flash_",
    "bios_",
    "partition_write_",
    "internal_disk_write_",
    "shell_",
)

_ACTION_META: dict[str, dict[str, Any]] = {
    "retry_readonly_probe": {
        "description": "Retry a failed read-only hardware/probe step",
        "rollback": "no_state_change_expected",
        "risk": "none",
    },
    "restart_setuphelfer_service": {
        "description": "Clean restart of Setuphelfer rescue service only",
        "rollback": "restore_previous_service_state",
        "risk": "low",
    },
    "kill_duplicate_setuphelfer_process": {
        "description": "Terminate duplicate Setuphelfer UI/backend process when identity is unambiguous",
        "rollback": "cannot_restore_killed_pid",
        "risk": "low",
    },
    "remount_detect_only": {
        "description": "Re-detect missing mount without writing internal disks",
        "rollback": "unmount_detect_mount_if_added",
        "risk": "none",
    },
    "reinit_network": {
        "description": "Re-initialize network interfaces / DHCP stack",
        "rollback": "restore_previous_network_state",
        "risk": "low",
    },
    "clear_soft_rfkill": {
        "description": "Clear soft rfkill block only (never hard-block override)",
        "rollback": "reapply_soft_rfkill_if_was_blocked",
        "risk": "low",
    },
    "activate_tui_fallback": {
        "description": "Activate temporary TUI/GUI fallback path",
        "rollback": "deactivate_tui_fallback",
        "risk": "low",
    },
    "plan_next_boot_profile_params": {
        "description": "Plan temporary next-boot profile/cmdline parameters (no immediate apply)",
        "rollback": "clear_planned_next_boot_params",
        "risk": "none",
    },
    "resolve_port_conflict_via_service_restart": {
        "description": "Resolve temporary port conflict via controlled service restart",
        "rollback": "restore_previous_service_state",
        "risk": "low",
    },
    "probe_load_reversible_kernel_module": {
        "description": "Probe-load an already-present alternative kernel module when explicitly reversible",
        "rollback": "unload_probed_module",
        "risk": "medium",
    },
}


def _is_forbidden(action_id: str) -> bool:
    aid = (action_id or "").strip().lower()
    if aid in ALLOWED_ACTIONS:
        return False
    for prefix in FORBIDDEN_ACTION_PREFIXES:
        if aid.startswith(prefix):
            return True
    # Explicit forbidden vocabulary even without prefix match.
    forbidden_tokens = (
        "apt",
        "dkms",
        "nvidia_proprietary",
        "firmware_flash",
        "bios",
        "partition_write",
        "internal_disk_write",
        "arbitrary_shell",
        "shell_exec",
    )
    return any(tok in aid for tok in forbidden_tokens)


def plan_remediation(
    action_id: str,
    *,
    reason: str,
    before_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Plan a remediation. Returns allowed flag and blockers; never executes."""
    aid = str(action_id or "").strip()
    before = dict(before_state or {})
    blockers: list[str] = []

    if not aid:
        blockers.append("missing_action_id")
    elif aid not in ALLOWED_ACTIONS:
        blockers.append("action_not_allowlisted")
        if _is_forbidden(aid):
            blockers.append("forbidden_destructive_or_uncontrolled_action")

    if not reason or not str(reason).strip():
        blockers.append("missing_reason")

    allowed = not blockers
    meta = _ACTION_META.get(aid, {})
    return {
        "action_id": aid,
        "reason": reason,
        "before_state": before,
        "allowed": allowed,
        "blockers": blockers,
        "action": meta.get("description"),
        "rollback": meta.get("rollback"),
        "risk": meta.get("risk"),
        "result": "planned" if allowed else "refused",
    }


def apply_remediation(
    action_id: str,
    *,
    reason: str,
    before_state: Mapping[str, Any] | None,
    executor: Callable[[str, Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Apply an allowlisted remediation.

    If ``action_id`` is not allowlisted the call is refused and ``executor``
    is never invoked. When allowed and an executor is provided, it is called
    with ``(action_id, before_state)`` and must return an ``after_state`` dict.
    """
    plan = plan_remediation(action_id, reason=reason, before_state=before_state)
    aid = plan["action_id"]
    before = plan["before_state"]
    meta = _ACTION_META.get(aid, {})

    base = {
        "action_id": aid,
        "reason": reason,
        "before_state": before,
        "action": meta.get("description") or aid,
        "after_state": dict(before),
        "rollback": meta.get("rollback") or "none",
        "result": "refused",
        "allowed": plan["allowed"],
        "blockers": list(plan["blockers"]),
    }

    if not plan["allowed"]:
        return base

    if executor is None:
        base["result"] = "planned_only"
        base["after_state"] = dict(before)
        return base

    after = executor(aid, before)
    if not isinstance(after, Mapping):
        base["result"] = "executor_invalid_return"
        base["blockers"] = list(base["blockers"]) + ["executor_must_return_mapping"]
        base["allowed"] = False
        return base

    base["after_state"] = dict(after)
    base["result"] = "applied"
    return base
