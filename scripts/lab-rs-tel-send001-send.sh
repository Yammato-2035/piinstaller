#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PYTHONPATH="$ROOT/backend" python3 - <<'PY'
import json
import sys

from core.rescue_stick_cloud_lab_config import rescue_stick_lab_send_config_from_env
from core.rescue_stick_cloud_lab_models import RescueStickLabSendStatus
from core.rescue_stick_cloud_lab_send import (
    evaluate_rescue_stick_lab_preconditions,
    execute_rescue_stick_lab_send,
    redact_secret_material,
)

preview_gate = evaluate_rescue_stick_lab_preconditions(rescue_stick_lab_send_config_from_env())
if preview_gate.send_status != RescueStickLabSendStatus.LAB_SEND_READY:
    print(
        redact_secret_material(
            json.dumps(
                {
                    "send_status": preview_gate.send_status.value,
                    "blocked": True,
                    "reason": "preconditions_not_met",
                },
                indent=2,
                sort_keys=True,
            )
        )
    )
    sys.exit(17)

result = execute_rescue_stick_lab_send()
print(redact_secret_material(json.dumps(result.to_dict(), indent=2, sort_keys=True)))
if result.send_status != RescueStickLabSendStatus.LAB_SEND_ACCEPTED:
    sys.exit(18)
PY
