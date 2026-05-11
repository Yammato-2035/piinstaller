# Rescue — ISO readiness pipeline (KB)

## Kurzüberblick

Der Runner `backend/deploy/runner_rescue_iso_readiness_pipeline.py` schreibt Handoffs unter `docs/evidence/runtime-results/handoff/` (`rescue_iso_baseline.json`, `rescue_iso_filesystem_layout.json`, `offline_recovery_runtime_validation.json`, `rescue_bootflow_simulation.json`, `rescue_iso_safety_validation.json`, `rescue_iso_final_readiness_gate.json`, `rescue_iso_build_plan.json`) und bindet bestehende Gates (`setuphelfer_branding_guard_check.json`, `runtime_identifier_zero_state_verification.json`, `rescue_final_recovery_readiness_gate.json`) ein.

## Verweise

- Deploy DE/EN: `docs/deploy/DEPLOY_RESCUE_ISO_READINESS_PIPELINE_DE.md` / `_EN.md`
- Evidence: `docs/evidence/DEPLOY_RESCUE_ISO_READINESS_PIPELINE.md`
