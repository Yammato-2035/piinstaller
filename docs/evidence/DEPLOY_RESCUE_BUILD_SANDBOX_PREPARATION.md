# Evidence — DEPLOY_RESCUE_BUILD_SANDBOX_PREPARATION

## Nachweisziel

Dokumentieren, dass die Build-Sandbox-Vorbereitung **nur** Verzeichnisse und JSON-Plaene unter `build/rescue/` sowie Safety-/Final-Gate-Handoffs erzeugt — ohne Build-Execute, ISO, VM oder privilegierte Systemoperationen.

## Tests

`backend/tests/test_deploy_runner_rescue_build_sandbox_preparation_v1.py` und die genannten Regressionen (Dry-Build-Orchestrierung, Runtime-Bundle-Manifest, Branding-Guard).
