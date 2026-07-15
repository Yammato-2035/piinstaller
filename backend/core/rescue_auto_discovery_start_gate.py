"""Discovery start gate for systemd ExecCondition (001D7B/001D7C)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from core.rescue_discovery_observability import ensure_boot_context, persist_start_gate_audit
from core.rescue_discovery_run_control import (
    load_discovery_run_control,
    validate_discovery_run_control,
)
from core.rescue_payload_version import rescue_payload_version
from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount
from core.rescue_run_mode import resolve_run_mode

EXIT_START = 0
EXIT_SKIP = 1
EXIT_CONFIG_ERROR = 2


def _cmdline_tokens() -> set[str]:
    try:
        raw = Path("/proc/cmdline").read_text(encoding="utf-8")
    except OSError:
        return set()
    return {tok for tok in raw.split() if tok}


def _machine_family_plausible(expected: str) -> bool:
    expected_l = expected.strip().lower()
    if not expected_l:
        return True
    paths = (
        Path("/sys/class/dmi/id/product_name"),
        Path("/sys/class/dmi/id/board_name"),
    )
    parts: list[str] = []
    for path in paths:
        try:
            parts.append(path.read_text(encoding="utf-8").strip())
        except OSError:
            continue
    hay = " ".join(parts).lower()
    return expected_l in hay if hay else True


def evaluate_discovery_start_gate(
    *,
    setup_logs_base: Path | None = None,
    cmdline: set[str] | None = None,
    payload_version: str | None = None,
) -> dict[str, Any]:
    tokens = cmdline if cmdline is not None else _cmdline_tokens()
    has_auto_discovery = "setuphelfer_auto_discovery=1" in tokens
    has_msi_lab = "setuphelfer_msi_lab_auto=1" in tokens
    actual = payload_version if payload_version is not None else rescue_payload_version()

    def _finish(result: dict[str, Any], *, control: dict[str, Any] | None = None) -> dict[str, Any]:
        enriched = {
            **result,
            "kernel_auto_discovery": has_auto_discovery,
            "run_control_found": control is not None,
            "run_control_enabled": bool(control.get("enabled")) if control else False,
            "run_control_consumed": bool(control.get("consumed")) if control else False,
            "payload_version": actual,
        }
        try:
            ensure_boot_context(payload_version=actual)
            persist_start_gate_audit(enriched, payload_version=actual)
        except OSError:
            pass
        return enriched

    if not has_auto_discovery and not has_msi_lab:
        return _finish(
            {
                "start_allowed": False,
                "reason": "kernel_trigger_missing",
                "exit_code": EXIT_SKIP,
                "run_mode": None,
                "payload_version_match": False,
            }
        )

    base = setup_logs_base or find_setup_logs_mount()
    if base is None:
        if has_auto_discovery:
            return _finish(
                {
                    "start_allowed": True,
                    "reason": "auto_discovery_flag_without_setup_logs_yet",
                    "exit_code": EXIT_START,
                    "run_mode": "auto_discovery_only",
                    "payload_version_match": True,
                }
            )
        return _finish(
            {
                "start_allowed": False,
                "reason": "discovery_run_control_unavailable",
                "exit_code": EXIT_SKIP,
                "run_mode": None,
                "payload_version_match": False,
            }
        )

    control = load_discovery_run_control(base)
    validation = validate_discovery_run_control(control)
    if not validation["ok"]:
        if has_auto_discovery and not control:
            return _finish(
                {
                    "start_allowed": False,
                    "reason": "discovery_run_control_missing",
                    "exit_code": EXIT_SKIP,
                    "run_mode": None,
                    "payload_version_match": False,
                },
                control=control,
            )
        code = str(validation.get("code") or "discovery_run_control_invalid")
        exit_code = EXIT_SKIP
        if "invalid_schema" in (validation.get("errors") or []):
            exit_code = EXIT_CONFIG_ERROR
        return _finish(
            {
                "start_allowed": False,
                "reason": code,
                "exit_code": exit_code,
                "run_mode": (control or {}).get("run_mode"),
                "payload_version_match": False,
                "errors": validation.get("errors") or [],
            },
            control=control,
        )

    assert control is not None
    expected = str(control.get("expected_payload_version") or "")
    payload_match = bool(expected) and expected == actual
    if not payload_match:
        return _finish(
            {
                "start_allowed": False,
                "reason": "payload_version_mismatch",
                "exit_code": EXIT_CONFIG_ERROR,
                "run_mode": control.get("run_mode"),
                "payload_version_match": False,
                "expected_payload_version": expected,
                "actual_payload_version": actual,
            },
            control=control,
        )

    family = str(control.get("expected_machine_family") or "")
    if family and not _machine_family_plausible(family):
        return _finish(
            {
                "start_allowed": False,
                "reason": "machine_family_mismatch",
                "exit_code": EXIT_CONFIG_ERROR,
                "run_mode": control.get("run_mode"),
                "payload_version_match": True,
            },
            control=control,
        )

    resolved = resolve_run_mode(setup_logs_base=base, discovery_control=control)
    if not resolved.get("ok"):
        return _finish(
            {
                "start_allowed": False,
                "reason": resolved.get("code") or "blocked_run_mode_conflict",
                "exit_code": EXIT_CONFIG_ERROR,
                "run_mode": resolved.get("run_mode"),
                "payload_version_match": True,
            },
            control=control,
        )
    if resolved.get("run_mode") != "auto_discovery_only":
        return _finish(
            {
                "start_allowed": False,
                "reason": "run_mode_not_auto_discovery_only",
                "exit_code": EXIT_SKIP,
                "run_mode": resolved.get("run_mode"),
                "payload_version_match": True,
            },
            control=control,
        )

    return _finish(
        {
            "start_allowed": True,
            "reason": "discovery_run_control_ready",
            "exit_code": EXIT_START,
            "run_mode": "auto_discovery_only",
            "payload_version_match": True,
        },
        control=control,
    )


def main(argv: list[str] | None = None) -> int:
    del argv
    result = evaluate_discovery_start_gate()
    print(
        json.dumps(
            {
                "start_allowed": result.get("start_allowed"),
                "reason": result.get("reason"),
                "run_mode": result.get("run_mode"),
                "payload_version_match": result.get("payload_version_match"),
                "exit_code": result.get("exit_code"),
            },
            ensure_ascii=False,
        )
    )
    return int(result.get("exit_code") or EXIT_SKIP)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
