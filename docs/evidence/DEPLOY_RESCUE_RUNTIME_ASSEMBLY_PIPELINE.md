# Evidence — DEPLOY_RESCUE_RUNTIME_ASSEMBLY_PIPELINE

## Nachweisziel

Dokumentieren, dass die Runtime-Assembly **nur** unter `build/rescue/runtime/` und in dokumentierten Handoff-Pfaden schreibt und keine ISO-/VM-/Restore-Ausführung auslöst.

## Tests

`backend/tests/test_deploy_runner_rescue_runtime_assembly_pipeline_v1.py` und Regressionen (Pseudo-Boot, Artefakt-Pipeline, Branding-Guard).
