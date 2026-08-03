"""
Driver activation plan — safety-gated preview wrapper around a DriverPlan.

PI-RS-HW-COMPAT-PROVISION-001 Phase 9 (activation plan half).

This module never activates anything. ``build_driver_activation_preview`` always
forces ``live_activation_possible = False`` and ``persistent_install_possible =
False`` regardless of what an upstream resolver produced, and
``validate_activation_plan_is_safe`` is a structural linter that fails loudly if a
forbidden action sneaks into a plan (defense in depth for PI-RS-HW-ACTIVATE-002's
future re-use of this shape).
"""

from __future__ import annotations

from typing import Any

DRIVER_ACTIVATION_PLAN_VERSION = 1

_FORBIDDEN_WARNING_MARKERS = ("curl|bash", "wget|sh", "auto_accept_license", "blacklist_modified")


def build_driver_activation_preview(driver_plan: dict[str, Any]) -> dict[str, Any]:
    """Wrap a resolver's DriverPlan as a preview-only activation plan."""
    preview = dict(driver_plan)
    preview["live_activation_possible"] = False
    preview["persistent_install_possible"] = False
    preview["write_allowed"] = False
    preview["requires_operator_confirmation"] = True
    preview["phase"] = "PI-RS-HW-COMPAT-PROVISION-001"
    preview["next_phase_for_real_activation"] = "PI-RS-HW-ACTIVATE-002"
    return preview


def validate_activation_plan_is_safe(plan: dict[str, Any]) -> list[str]:
    """Return a list of safety violations (empty == safe). Never raises — callers
    decide whether a non-empty result blocks anything."""
    violations: list[str] = []
    if plan.get("live_activation_possible") is True:
        violations.append("live_activation_possible_must_be_false_in_this_phase")
    if plan.get("persistent_install_possible") is True:
        violations.append("persistent_install_possible_must_be_false_in_this_phase")
    if plan.get("write_allowed") is True:
        violations.append("write_allowed_must_be_false_in_this_phase")
    for warning in plan.get("warnings") or []:
        if any(marker in str(warning) for marker in _FORBIDDEN_WARNING_MARKERS):
            violations.append(f"forbidden_action_marker_in_warnings:{warning}")
    if plan.get("license_review_required") and plan.get("errors") == [] and plan.get("auto_accepted_license"):
        violations.append("license_must_not_be_auto_accepted")
    return violations


def build_driver_activation_plan_diagnostics() -> dict[str, Any]:
    return {
        "plan_version": DRIVER_ACTIVATION_PLAN_VERSION,
        "module": "core.driver_activation_plan",
        "write_allowed": False,
        "live_activation_possible": False,
        "persistent_install_possible": False,
    }


__all__ = [
    "DRIVER_ACTIVATION_PLAN_VERSION",
    "build_driver_activation_preview",
    "validate_activation_plan_is_safe",
    "build_driver_activation_plan_diagnostics",
]
