"""
Rescue master assessment bundle V1 — combines assessment, network, telemetry, safe actions.
Read-only aggregation for API and evidence export.
"""

from __future__ import annotations

import os
from typing import Any

from core.rescue_network_connectivity_v2 import build_network_connectivity_v2
from core.rescue_repair_advice_engine_v1 import build_safe_action_plan
from core.rescue_system_assessment_v2 import build_system_assessment_v2
from core.rescue_telemetry_connectivity_v1 import build_telemetry_connectivity_v1


def _project_version() -> str:
  try:
    from pathlib import Path
    import json

    path = Path(__file__).resolve().parents[2] / "config" / "version.json"
    if path.is_file():
      return str(json.loads(path.read_text(encoding="utf-8")).get("project_version") or "unknown")
  except (OSError, json.JSONDecodeError, ValueError):
    pass
  return os.environ.get("SETUPHELFER_RESCUE_VERSION", "unknown")


def build_master_assessment_bundle_v1() -> dict[str, Any]:
  version = _project_version()
  assessment = build_system_assessment_v2(rescue_version=version)
  network = build_network_connectivity_v2()
  telemetry = build_telemetry_connectivity_v1(
    mode=os.environ.get("RESCUE_TELEMETRY_CONNECTIVITY_MODE", "auto")
  )
  issue_codes = sorted(
    set(assessment.get("issue_codes") or [])
    | set(network.get("issue_codes") or [])
    | set(telemetry.get("issue_codes") or [])
  )
  plan = build_safe_action_plan(
    issue_codes,
    assessment.get("recommendation_codes"),
  )
  return {
    "schema_version": "rescue.master_assessment_bundle.v1",
    "rescue_version": version,
    "system_assessment": assessment,
    "network_connectivity": network,
    "telemetry_connectivity": telemetry,
    "safe_action_plan": plan,
    "issue_codes": issue_codes,
  }
