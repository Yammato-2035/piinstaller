"""Physical E2E start gate — blocks auto_discovery_only (001D7B)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount
from core.rescue_run_mode import physical_e2e_start_allowed

EXIT_START = 0
EXIT_SKIP = 1
EXIT_CONFIG_ERROR = 2


def evaluate_physical_e2e_start_gate(
    *,
    setup_logs_base: Path | None = None,
) -> dict[str, Any]:
    base = setup_logs_base or find_setup_logs_mount()
    decision = physical_e2e_start_allowed(setup_logs_base=base)
    if decision.get("physical_e2e_start_allowed"):
        return {
            **decision,
            "exit_code": EXIT_START,
        }
    reason = str(decision.get("reason") or "skipped_by_run_mode")
    exit_code = EXIT_CONFIG_ERROR if reason == "blocked_run_mode_conflict" else EXIT_SKIP
    return {
        **decision,
        "exit_code": exit_code,
    }


def main(argv: list[str] | None = None) -> int:
    del argv
    result = evaluate_physical_e2e_start_gate()
    print(
        json.dumps(
            {
                "physical_e2e_start_allowed": result.get("physical_e2e_start_allowed"),
                "reason": result.get("reason"),
                "run_mode": result.get("run_mode"),
                "skip_class": result.get("skip_class") or "",
            },
            ensure_ascii=False,
        )
    )
    return int(result.get("exit_code") or EXIT_SKIP)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
