# KB: DEPLOY_RUNNER_HANDOFF

## Überblick

Backend erzeugt und persistiert Runner-Jobs unter `runner-jobs/`, startet den Runner nur im Dry-run und verarbeitet die strukturierte JSON-Antwort.

## Sicherheitsmerkmale

- Vorbedingungen: Guard READY, Final Confirmation READY, Hardware Gate `test_ready`
- Atomisches Jobfile-Write (`.tmp` → `replace`)
- Pfad-Containment und Symlink-/Traversal-Blockade
- Runner-Start nur mit festen Argumenten und `shell=False`
- Timeout (30 Sekunden)
- Audit-Eintrag bei Create/Execute

## API

Route: `POST /api/deploy/runner/handoff`

Pflichtfelder:
- `final_confirmation_result`
- `real_write_guard_result`
- `hardware_gate_report`
- `image_inspect_result`
- `write_plan`
- `write_execute_result`

## Verwandt

- `docs/deploy/DEPLOY_RUNNER_HANDOFF_DE.md` / `_EN.md`
- `docs/deploy/DEPLOY_WRITE_RUNNER_CONTRACT_DE.md`
- `docs/evidence/DEPLOY_RUNNER_HANDOFF_RUNTIME.md`
