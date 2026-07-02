#!/usr/bin/env bash
# Collect system assessment V2 evidence on rescue stick (read-only).
# Output only under SETUP_LOGS — no target disk writes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EVIDENCE_ROOT="${SETUP_LOGS:-/run/setuphelfer}/setuphelfer/evidence/system-assessment"
mkdir -p "$EVIDENCE_ROOT"
export PYTHONPATH="${REPO_ROOT}/backend:${PYTHONPATH:-}"

python3 <<PY
import json
import os
from pathlib import Path

from core.rescue_system_assessment_v2 import build_system_assessment_v2

root = Path(os.environ.get("EVIDENCE_ROOT", "${EVIDENCE_ROOT}"))
result = build_system_assessment_v2()
(root / "system-assessment-v2.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
)
issue_codes = ", ".join(result.get("issue_codes") or [])
md = f"# System Assessment V2\\n\\nIssue codes: {issue_codes}\\n"
(root / "system-assessment-v2.md").write_text(md, encoding="utf-8")
(root / "system-assessment-redaction-report.json").write_text(
    json.dumps(result.get("redaction_report") or {}, indent=2), encoding="utf-8"
)
print(root / "system-assessment-v2.json")
PY
