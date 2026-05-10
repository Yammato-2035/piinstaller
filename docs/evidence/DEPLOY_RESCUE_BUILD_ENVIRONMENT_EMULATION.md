# Evidence — Deploy Rescue Build Environment Emulation

## Scope

- Emulation JSONs: `build/rescue/emulation/*.json` (Snapshot, Workspace, Outputs, Logs, Overlay, Seal)
- Handoffs: `docs/evidence/runtime-results/handoff/rescue_build_emulation_verify.json`, `rescue_build_emulation_final_gate.json`

## Runner

`backend/deploy/runner_rescue_build_environment_emulation.py` — keine Subprozesse, kein `mount(`, kein `chroot(`; Verify lehnt Nicht-JSON-Dateien im Emulationsverzeichnis und verbotene Token in den JSON-Inhalten ab.

## API

Siehe Deploy-Doku DE/EN fuer Routen und Codes.
