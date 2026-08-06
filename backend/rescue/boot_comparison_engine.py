"""
Boot comparison / causality engine for sequential ASUS boot profiles.

PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003 Phase 8.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


_COMPARE_KEYS = (
    "boot_profile",
    "payload_version",
    "git_commit",
    "kernel_version",
    "initramfs_hash",
    "cmdline",
    "bios_version",
    "secure_boot_status",
    "last_successful_marker",
    "first_failed_marker",
)


def compare_boot_runs(previous: Mapping[str, Any] | None, current: Mapping[str, Any]) -> dict[str, Any]:
    prev = dict(previous or {})
    cur = dict(current)
    unchanged = []
    changed = []
    for key in _COMPARE_KEYS:
        if key not in cur and key not in prev:
            continue
        if prev.get(key) == cur.get(key):
            unchanged.append(key)
        else:
            changed.append(
                {
                    "factor": key,
                    "previous": prev.get(key),
                    "current": cur.get(key),
                }
            )

    prev_devices = set(prev.get("device_ids") or [])
    cur_devices = set(cur.get("device_ids") or [])
    prev_drivers = set(prev.get("bound_drivers") or [])
    cur_drivers = set(cur.get("bound_drivers") or [])
    prev_fw_err = set(prev.get("firmware_errors") or [])
    cur_fw_err = set(cur.get("firmware_errors") or [])
    prev_kernel = set(prev.get("kernel_messages") or [])
    cur_kernel = set(cur.get("kernel_messages") or [])

    causality = _estimate_causality(changed, cur)
    next_boot = cur.get("recommended_next_boot_profile") or _default_next_profile(cur)

    return {
        "unchanged_factors": unchanged,
        "changed_factors": changed,
        "new_devices": sorted(cur_devices - prev_devices),
        "missing_devices": sorted(prev_devices - cur_devices),
        "newly_bound_drivers": sorted(cur_drivers - prev_drivers),
        "new_firmware_errors": sorted(cur_fw_err - prev_fw_err),
        "resolved_firmware_errors": sorted(prev_fw_err - cur_fw_err),
        "new_kernel_messages": sorted(cur_kernel - prev_kernel)[:50],
        "boot_stage_delta": {
            "previous_last_ok": prev.get("last_successful_marker"),
            "current_last_ok": cur.get("last_successful_marker"),
            "previous_first_fail": prev.get("first_failed_marker"),
            "current_first_fail": cur.get("first_failed_marker"),
        },
        "causality_assessment": causality["assessment"],
        "root_cause_confidence": causality["confidence"],
        "hypothesis": causality["hypothesis"],
        "recommended_next_boot": next_boot,
        "simultaneous_change_violation": _simultaneous_change_violation(changed),
    }


def _estimate_causality(changed: Sequence[Mapping[str, Any]], current: Mapping[str, Any]) -> dict[str, Any]:
    factors = [c["factor"] for c in changed]
    if not factors:
        return {
            "assessment": "no_material_change",
            "confidence": 0.2,
            "hypothesis": "repeat_same_profile_for_reproducibility",
        }
    if factors == ["boot_profile"]:
        return {
            "assessment": "boot_profile_change_primary",
            "confidence": 0.7,
            "hypothesis": f"outcome delta attributable to profile {current.get('boot_profile')}",
        }
    if "cmdline" in factors and "boot_profile" in factors:
        return {
            "assessment": "cmdline_tied_to_profile",
            "confidence": 0.65,
            "hypothesis": "profile cmdline is the intended single variable",
        }
    if len(factors) > 1 and any(f in factors for f in ("kernel_version", "payload_version", "bios_version")):
        return {
            "assessment": "multi_factor_change_review_required",
            "confidence": 0.3,
            "hypothesis": "do_not_attribute_root_cause_until_single_variable_rerun",
        }
    return {
        "assessment": "partial_factor_change",
        "confidence": 0.45,
        "hypothesis": f"investigate_changed_factors:{','.join(factors)}",
    }


def _simultaneous_change_violation(changed: Sequence[Mapping[str, Any]]) -> bool:
    """True if kernel + graphics cmdline + packages/firmware/bios changed together."""
    factors = {c["factor"] for c in changed}
    heavy = {"kernel_version", "cmdline", "bios_version", "payload_version"}
    return len(factors & heavy) >= 3


def _default_next_profile(current: Mapping[str, Any]) -> str:
    profile = str(current.get("boot_profile") or "ASUS-00")
    order = ["ASUS-00", "ASUS-01", "ASUS-02", "ASUS-03", "ASUS-04", "ASUS-05"]
    if current.get("first_failed_marker"):
        return "ASUS-RECOVERY" if profile != "ASUS-00" else "ASUS-00"
    if profile in order:
        idx = order.index(profile)
        if idx + 1 < len(order):
            return order[idx + 1]
    return "ASUS-RECOVERY"


def assert_single_variable_hypothesis(plan: Mapping[str, Any]) -> list[str]:
    """Return errors if a next-boot plan changes more than one primary variable."""
    errors: list[str] = []
    changed = list(plan.get("intended_changed_variables") or [])
    if not changed:
        errors.append("missing_hypothesis_changed_variable")
    if len(changed) > 1:
        errors.append("multiple_primary_variables_forbidden")
    if not plan.get("hypothesis"):
        errors.append("missing_hypothesis")
    if not plan.get("expected_outcome"):
        errors.append("missing_expected_outcome")
    if not plan.get("fallback_profile"):
        errors.append("missing_fallback_profile")
    return errors
