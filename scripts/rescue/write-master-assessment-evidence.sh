#!/usr/bin/env bash
# Write master assessment evidence under SETUP_LOGS (rescue stick / lab).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EVIDENCE_ROOT="${SETUP_LOGS:-/run/setuphelfer}/setuphelfer/evidence"
export PYTHONPATH="${REPO_ROOT}/backend:${PYTHONPATH:-}"

mkdir -p \
  "${EVIDENCE_ROOT}/system-assessment" \
  "${EVIDENCE_ROOT}/network" \
  "${EVIDENCE_ROOT}/safe-actions"

python3 <<PY
import json
import os
from pathlib import Path

from core.rescue_master_assessment_bundle_v1 import build_master_assessment_bundle_v1
from core.rescue_network_connectivity_v2 import build_network_connectivity_v2
from core.rescue_repair_advice_engine_v1 import build_safe_action_plan
from core.rescue_system_assessment_v2 import build_system_assessment_v2
from core.rescue_telemetry_connectivity_v1 import build_telemetry_connectivity_v1

root = Path(os.environ.get("EVIDENCE_ROOT", "${EVIDENCE_ROOT}"))

assessment = build_system_assessment_v2()
(root / "system-assessment/system-assessment-v2.json").write_text(
    json.dumps(assessment, indent=2, ensure_ascii=False), encoding="utf-8"
)
(root / "system-assessment/system-assessment-redaction-report.json").write_text(
    json.dumps(assessment.get("redaction_report") or {}, indent=2), encoding="utf-8"
)

network = build_network_connectivity_v2()
(root / "network/network-connectivity-v2.json").write_text(
    json.dumps(network, indent=2, ensure_ascii=False), encoding="utf-8"
)

telemetry = build_telemetry_connectivity_v1()
(root / "network/telemetry-connectivity-v1.json").write_text(
    json.dumps(telemetry, indent=2, ensure_ascii=False), encoding="utf-8"
)

plan = build_safe_action_plan(
    assessment.get("issue_codes") or [],
    assessment.get("recommendation_codes"),
)
(root / "safe-actions/safe-action-plan.json").write_text(
    json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8"
)

bundle = build_master_assessment_bundle_v1()
(root / "master-assessment-bundle-v1.json").write_text(
    json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(root)
PY
