# Deploy — Rescue ISO Build & VM Validation (DE)

Phase 1: **echte ISO-Erstellung** und **VM-Validierung** sind erlaubt, weiterhin ohne USB-Flash, ohne Restore-Execute und ohne Writes auf interne Host-Datenträger durch die Runner.

## Workspace

Siehe `docs/developer/RESCUE_BUILD_WORKSPACE_POLICY.md` und `docs/developer/RESCUE_VM_TEST_SAFETY_POLICY.md`. Artefakte nur unter `build/rescue/`.

## Handoff-Dateien

| Zweck | JSON |
|--------|------|
| Live-build-Konfig (Manifest) | `docs/evidence/runtime-results/handoff/rescue_live_build_config.json` |
| ISO-Ausführungsplan | `docs/evidence/runtime-results/handoff/rescue_iso_execution_plan.json` |
| ISO-Build-Precheck | `docs/evidence/runtime-results/handoff/rescue_iso_build_precheck.json` |
| ISO-Build-Ergebnis | `docs/evidence/runtime-results/handoff/rescue_iso_build_result.json` |
| VM-Testplan | `docs/evidence/runtime-results/handoff/rescue_vm_test_plan.json` |
| VM-Testergebnis | `docs/evidence/runtime-results/handoff/rescue_vm_test_result.json` |
| ISO-Live-Runtime-Probe | `docs/evidence/runtime-results/handoff/rescue_iso_live_runtime_probe_plan.json` / `..._result.json` |
| ISO-Readiness-Gate | `docs/evidence/runtime-results/handoff/rescue_iso_readiness_gate.json` |

## API (`POST /api/deploy/rescue/...`)

- `live-build-config` — generiert nur JSON-Konfiguration
- `iso-execution-plan` — Schritte, Limits, verbotene Befehle
- `iso-build-precheck` — optional `min_free_disk_bytes`
- `iso-build-execute` — `explicit_execute_iso_build` **und** `explicit_rescue_build_approved` erforderlich
- `vm-test-plan` / `vm-test-execute`
- `iso-live-runtime-probe` — Body: `action`: `plan` \| `execute` \| `result`, plus Execute-Flags
- `iso-readiness-gate`

Skript: `scripts/rescue/build-rescue-iso-controlled.sh` — echtes `lb build` nur bei `SETUPHELFER_RESCUE_BUILD_APPROVED=1` und materialisierter `build/rescue/live-build/auto/config`.

## Version

Nach erfolgreichem Gate (ISO + VM + Readonly-Probe + Branding ok): manuell **1.7.x → 1.8.0** empfohlen — nicht automatisch.
