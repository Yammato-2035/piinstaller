"""Export PI-RS-TEL-001 evidence artifacts (redacted, no secrets)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.rescue_lab_telemetry_model import (
    RESCUE_LAB_PAYLOAD_KIND,
    RESCUE_LAB_PRODUCT,
    build_synthetic_rescue_lab_payload,
    validate_rescue_lab_payload_no_pii,
)
from core.rescue_lab_telemetry_status import build_rescue_lab_telemetry_dashboard_status, export_redacted_config_status

EVIDENCE_DIR = Path(__file__).resolve().parents[2] / "docs/evidence/pi_rs_tel_001_rescue_lab_telemetry_send_flow"


def _payload_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PI-RS-TEL-001 Rescue Lab Telemetry Payload",
        "type": "object",
        "required": [
            "product",
            "source",
            "environment",
            "payload_kind",
            "created_for",
            "rescue_preview",
            "safety",
        ],
        "properties": {
            "product": {"const": RESCUE_LAB_PRODUCT},
            "source": {"const": "rescue_stick_lab_preview"},
            "environment": {"const": "lab"},
            "payload_kind": {"const": RESCUE_LAB_PAYLOAD_KIND},
            "created_for": {"const": "PI-RS-TEL-001"},
            "rescue_preview": {
                "type": "object",
                "required": ["stick_version", "runtime_mode", "network_state", "send_flow"],
            },
            "safety": {
                "type": "object",
                "required": [
                    "contains_real_host_data",
                    "contains_raw_logs",
                    "contains_secrets",
                    "contains_mac_addresses",
                    "contains_ip_addresses",
                    "production_ready",
                ],
                "properties": {"production_ready": {"const": False}},
            },
        },
        "additionalProperties": True,
    }


def export_pi_rs_tel_001_evidence(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    out = root / "docs/evidence/pi_rs_tel_001_rescue_lab_telemetry_send_flow"
    out.mkdir(parents=True, exist_ok=True)

    payload = build_synthetic_rescue_lab_payload().to_dict()
    ok, violations = validate_rescue_lab_payload_no_pii(payload)

    (out / "rescue_lab_payload_schema.json").write_text(
        json.dumps(_payload_schema(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out / "rescue_lab_payload_synthetic_example.redacted.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out / "rescue_lab_no_pii_validation.json").write_text(
        json.dumps({"valid": ok, "violations": violations}, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "rescue_lab_client_config_status.json").write_text(
        json.dumps(export_redacted_config_status(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    dashboard = build_rescue_lab_telemetry_dashboard_status()
    dashboard.pop("last_result", None)
    (out / "rescue_lab_dashboard_status.json").write_text(
        json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    last = build_rescue_lab_telemetry_dashboard_status().get("last_result")
    redacted_last = last or {"status": "pending", "production_ready": False}
    (out / "rescue_lab_send_last_result.redacted.json").write_text(
        json.dumps(redacted_last, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out
