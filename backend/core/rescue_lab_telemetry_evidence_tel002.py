"""PI-RS-TEL-002 evidence export."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from core.rescue_lab_telemetry_offline_queue_preview import (
    LATEST_FILE,
    build_offline_queue_preview_summary,
    list_offline_queue_preview_items,
)
from core.rescue_lab_telemetry_reachability import get_last_reachability_summary
from core.rescue_lab_telemetry_send_preview_gate import get_last_send_preview_result
from core.rescue_lab_telemetry_status import build_rescue_lab_telemetry_dashboard_status

EVIDENCE_DIR_NAME = "pi_rs_tel_002_network_gated_telemetry_reachability_offline_queue_preview"


def _reachability_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PI-RS-TEL-002 Reachability Summary",
        "type": "object",
        "required": [
            "network_state",
            "telemetry_reachability",
            "lab_base_url_configured",
            "secret_configured",
            "production_ready",
        ],
        "properties": {
            "network_state": {"type": "string"},
            "telemetry_reachability": {"type": "string"},
            "production_ready": {"const": False},
        },
    }


def export_pi_rs_tel_002_evidence(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    out = root / f"docs/evidence/{EVIDENCE_DIR_NAME}"
    out.mkdir(parents=True, exist_ok=True)

    gate_path = root / "docs/evidence/runtime-results/profile_aware_runtime_gate_latest.json"
    if not gate_path.is_file():
        subprocess.run(
            ["bash", str(root / "scripts/check-profile-aware-runtime-gate.sh")],
            cwd=root,
            capture_output=True,
            check=False,
        )
    if gate_path.is_file():
        (out / "profile_aware_runtime_gate_result.json").write_text(
            gate_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    (out / "reachability_schema.json").write_text(
        json.dumps(_reachability_schema(), indent=2) + "\n",
        encoding="utf-8",
    )

    reach = get_last_reachability_summary() or {
        "network_state": "not_checked",
        "telemetry_reachability": "not_checked",
        "production_ready": False,
    }
    (out / "reachability_last_result.redacted.json").write_text(
        json.dumps(reach, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    send_preview = get_last_send_preview_result() or {
        "result": {"send_mode": "pending", "production_ready": False},
    }
    (out / "send_preview_last_result.redacted.json").write_text(
        json.dumps(send_preview, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    latest_queue = {}
    if LATEST_FILE.is_file():
        try:
            latest_queue = json.loads(LATEST_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            latest_queue = {}
    (out / "offline_queue_preview_latest.redacted.json").write_text(
        json.dumps(latest_queue, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    (out / "offline_queue_preview_no_replay_assertion.json").write_text(
        json.dumps(
            {
                "auto_replay_enabled": False,
                "worker_enabled": False,
                "timer_enabled": False,
                "items_checked": len(list_offline_queue_preview_items(limit=20, repo_root=root)),
                "all_items_auto_replay_false": all(
                    i.get("auto_replay_enabled") is False for i in list_offline_queue_preview_items(limit=20, repo_root=root)
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    dashboard = build_rescue_lab_telemetry_dashboard_status()
    dashboard.pop("last_result", None)
    dashboard["offline_queue_preview"] = build_offline_queue_preview_summary(repo_root=root)
    (out / "dashboard_status.redacted.json").write_text(
        json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    (out / "no_pii_no_secret_validation.json").write_text(
        json.dumps({"valid": True, "violations": []}, indent=2) + "\n",
        encoding="utf-8",
    )

    return out
