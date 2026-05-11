# Evidence — DEPLOY_RESCUE_RUNTIME_BUNDLE_MANIFEST

## Nachweisziel

Dokumentieren, dass Bundle-Inventar, Hash-Manifest und Seal **nur** unter `build/rescue/` (plus Konsistenz-Handoff) entstehen und keine ISO-/VM-/Execute-Schritte auslösen.

## Tests

`backend/tests/test_deploy_runner_rescue_runtime_bundle_manifest_v1.py` und Regressionen (Runtime-Assembly, Pseudo-Boot, Branding-Guard).
