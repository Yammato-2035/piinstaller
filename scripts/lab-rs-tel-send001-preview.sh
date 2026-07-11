#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PYTHONPATH="$ROOT/backend" python3 - <<'PY'
import json

from core.rescue_stick_cloud_lab_send import preview_rescue_stick_lab_send, redact_secret_material

result = preview_rescue_stick_lab_send()
print(redact_secret_material(json.dumps(result.to_dict(), indent=2, sort_keys=True)))
PY
