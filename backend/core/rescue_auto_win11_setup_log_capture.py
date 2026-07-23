"""Autonomous Windows Setup log capture when rescue boots on Gabriel G513QM.

Diagnostics-only: never enables storage/firmware/install writes.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from core.rescue_machine_identity_profiles import (
    GABRIEL_OPERATOR_PHRASE,
    is_known_developer_asus,
    read_dmi_fields,
)

SCHEMA_VERSION = 1
CONTRACT_VERSION = 1
DONE_MARKER = Path("/run/setuphelfer-rescue/auto-win11-setup-log-capture.done")


def _cmdline_has(flag: str, cmdline: str) -> bool:
    return bool(re.search(rf"(^| ){re.escape(flag)}=1( |$)", cmdline or ""))


def is_g513qm_dmi(dmi: Mapping[str, str] | None = None) -> bool:
    fields = dict(dmi or read_dmi_fields())
    board = str(fields.get("board_name") or "").upper()
    product = str(fields.get("product_name") or "").upper()
    return "G513QM" in board or "G513QM" in product


def evaluate_auto_win11_setup_log_gate(
    *,
    cmdline: str | None = None,
    dmi: Mapping[str, str] | None = None,
    done_marker: Path | None = None,
) -> dict[str, Any]:
    """Return whether the oneshot should run (systemd ExecCondition)."""
    cmd = cmdline if cmdline is not None else (
        Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace")
        if Path("/proc/cmdline").is_file()
        else ""
    )
    fields = dict(dmi or read_dmi_fields())
    marker = done_marker or DONE_MARKER
    reasons: list[str] = []

    if marker.is_file():
        return {
            "schema_version": SCHEMA_VERSION,
            "contract_version": CONTRACT_VERSION,
            "should_run": False,
            "reason": "already_done_this_boot",
            "reasons": ["already_done_this_boot"],
            "operator_phrase": GABRIEL_OPERATOR_PHRASE,
        }

    if not _cmdline_has("setuphelfer_rescue", cmd) and not _cmdline_has("setuphelfer_start_assistant", cmd):
        reasons.append("not_rescue_boot")
    if _cmdline_has("setuphelfer_msi_e2e_auto", cmd) or _cmdline_has("setuphelfer_msi_lab_auto", cmd):
        reasons.append("msi_lab_or_e2e_active")
    if is_known_developer_asus(fields):
        reasons.append("developer_asus_blocked")
    if not is_g513qm_dmi(fields):
        reasons.append("not_g513qm")

    # Prefer explicit flags; still allow plain rescue boot on G513QM so the stick
    # collects alone when returned to Gabriel without menu navigation.
    explicit = (
        _cmdline_has("setuphelfer_auto_win11_setup_logs", cmd)
        or _cmdline_has("setuphelfer_hardware_discovery", cmd)
    )
    if reasons:
        return {
            "schema_version": SCHEMA_VERSION,
            "contract_version": CONTRACT_VERSION,
            "should_run": False,
            "reason": reasons[0],
            "reasons": reasons,
            "explicit_flag": explicit,
            "operator_phrase": GABRIEL_OPERATOR_PHRASE,
            "product_name": fields.get("product_name") or "",
            "board_name": fields.get("board_name") or "",
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "should_run": True,
        "reason": "g513qm_auto_diagnostics" if not explicit else "explicit_cmdline_and_g513qm",
        "reasons": [],
        "explicit_flag": explicit,
        "operator_phrase": GABRIEL_OPERATOR_PHRASE,
        "product_name": fields.get("product_name") or "",
        "board_name": fields.get("board_name") or "",
        "auto_gabriel_bind": True,
        "write_allowed": False,
    }


def main() -> int:
    """CLI for systemd ExecCondition: exit 0 = run, exit 1 = skip."""
    import json
    import sys

    result = evaluate_auto_win11_setup_log_gate()
    out = Path("/run/setuphelfer-rescue")
    try:
        out.mkdir(parents=True, exist_ok=True)
        (out / "auto-win11-setup-log-gate.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except OSError:
        pass
    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    return 0 if result.get("should_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
