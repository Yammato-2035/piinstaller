# Evidence — DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_INPUTS

## Nachweisziel

Dokumentieren, dass Debian-Live-**Build-Eingaben** nur als Text/Manifeste unter `build/rescue/debian-live/` und als Safety-/Final-Gate-Handoffs unter `docs/evidence/runtime-results/handoff/` entstehen — **ohne** `live-build`/`lb build`, **ohne** ISO/IMG-Erzeugung in dieser Phase.

## Tests

`backend/tests/test_deploy_runner_rescue_debian_live_build_inputs_v1.py` und Regressionen: `test_deploy_runner_rescue_runtime_bundle_manifest_v1`, `test_deploy_runner_rescue_runtime_assembly_pipeline_v1`, `test_deploy_runner_setuphelfer_branding_guard_v1`.
