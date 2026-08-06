# Worktree Drift before persistent move

Generated: 2026-08-06T21:37:13+02:00
HEAD: 8672de4ca2239256895dc6a75c0ce86cc59c605b
Branch: pi-rs-asus-emergency-linux-telemetry-003
Path: /tmp/piinstaller-asus-emergency-linux-telemetry-003

## git status --short
```
 M docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json
 M docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md
 M docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md
 M docs/evidence/pi_rs_tel_001_rescue_lab_telemetry_send_flow/rescue_lab_payload_synthetic_example.redacted.json
 M docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json
 M docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview/queue_preview_latest.redacted.json
 M docs/evidence/runtime-results/rescue/live_build_dpkg_preflight_latest.json
?? backend/docs/
?? docs/evidence/rescue/asus-emergency-linux-003/worktree_drift_before_persistent_move_20260806T1936Z/
?? docs/evidence/runtime-results/handoff/rescue_storage_discovery_plan.json
?? docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json
?? docs/evidence/runtime-results/hardware/
?? docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview/queue_preview_items/8f6b931e-7db8-45f6-a7f7-2f9b6bfba860.redacted.json
?? docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview/queue_preview_items/e40c3fd1-8e91-467f-acdb-34c0e10a676a.redacted.json
```

## Modified tracked files (diffstat)
```
 .../lab-acceptance/LAB_ACCEPTANCE_REPORT.json      |  2 +-
 .../lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md     |  2 +-
 .../lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md     |  2 +-
 ...cue_lab_payload_synthetic_example.redacted.json |  2 +-
 .../handoff/legacy_identifier_inventory.json       | 50 +++++++++++-----------
 .../queue_preview_latest.redacted.json             | 14 +++---
 .../rescue/live_build_dpkg_preflight_latest.json   | 28 ++++++------
 7 files changed, 52 insertions(+), 48 deletions(-)
```

## Untracked
```
backend/docs/
docs/evidence/rescue/asus-emergency-linux-003/worktree_drift_before_persistent_move_20260806T1936Z/
docs/evidence/runtime-results/handoff/rescue_storage_discovery_plan.json
docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json
docs/evidence/runtime-results/hardware/
docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview/queue_preview_items/8f6b931e-7db8-45f6-a7f7-2f9b6bfba860.redacted.json
docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview/queue_preview_items/e40c3fd1-8e91-467f-acdb-34c0e10a676a.redacted.json
```
