#!/usr/bin/env bash
# Aggregate test runner for DCC-VIS-001 and core gates.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== DCC-VIS-001 frontend tests =="
cd frontend && npm test -- --run \
  src/dcc/visibility/runtimeStatusModel.test.ts \
  src/dcc/visibility/changelogModel.test.ts \
  src/lib/devDashboard/loadDevDashboard.test.ts \
  src/lib/devDashboard/governanceMatrix.test.ts \
  src/components/AppLanguageSwitcher.test.ts

echo "== DCC-VIS-001 safety gate =="
bash "$ROOT/scripts/check-dcc-vis-001-safety.sh"

echo "== version consistency =="
python3 "$ROOT/backend/tools/check_version_consistency.py" --repo-root "$ROOT"

echo "run-tests.sh: ok"
