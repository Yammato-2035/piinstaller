# Evidence — Deploy Rescue Sandbox Controlled Copy

## Scope

Evidence-Handoffs unter `docs/evidence/runtime-results/handoff/`:

- `rescue_sandbox_copy_execution_precheck.json`
- `rescue_sandbox_copy_verify_result.json`
- `rescue_sandbox_copy_final_gate.json`

Build-Artefakte unter `build/rescue/sandbox/manifests/`:

- `config_copy_result.json`
- `runtime_copy_result.json`
- `sandbox_copy.seal.json`

## Runner

`backend/deploy/runner_rescue_sandbox_controlled_copy.py` — keine Subprozesse, kein `mount(`, kein `chroot(`; nur Pfad-/JSON-/Datei-IO innerhalb des Repos.

## API

Siehe `docs/deploy/DEPLOY_RESCUE_SANDBOX_CONTROLLED_COPY_DE.md` bzw. `_EN.md` fuer Routen und Response-Codes.
