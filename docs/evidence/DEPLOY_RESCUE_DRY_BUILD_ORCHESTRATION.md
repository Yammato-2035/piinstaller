# Evidence — DEPLOY_RESCUE_DRY_BUILD_ORCHESTRATION

## Nachweisziel

Dokumentieren, dass die Rescue-Dry-Build-Orchestrierung **nur** strukturierte JSON-Artefakte und Handoffs erzeugt — ohne Build-Execute, ohne ISO-Output, ohne VM/QEMU und ohne privilegierte Installationspfade aus der API.

## Tests

`backend/tests/test_deploy_runner_rescue_dry_build_orchestration_v1.py` und Regressionen: Debian-Live-Build-Inputs, Runtime-Bundle-Manifest, Branding-Guard.
