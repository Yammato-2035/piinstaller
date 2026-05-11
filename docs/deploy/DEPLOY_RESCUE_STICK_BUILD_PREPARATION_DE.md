# Deploy — Rescue Stick Build Preparation (DE)

Read-only **Deploy-Runner** und API-Endpunkte fuer die Vorbereitung des Setuphelfer-Rettungssticks (kein ISO-Build, kein USB-Write).

## Handoff-Dateien

| Schritt | JSON |
|--------|------|
| Live-OS-Basisentscheidung | `docs/evidence/runtime-results/handoff/rescue_live_os_base_decision.json` |
| Komponenten-Inventar | `docs/evidence/runtime-results/handoff/rescue_stick_component_inventory.json` |
| MVP-Scope-Gate | `docs/evidence/runtime-results/handoff/rescue_mvp_scope_gate.json` |
| Debian-Live-Buildplan | `docs/evidence/runtime-results/handoff/rescue_debian_live_build_plan.json` |
| ISO-Testmatrix | `docs/evidence/runtime-results/handoff/rescue_iso_test_matrix.json` |
| Build-Readiness-Gate | `docs/evidence/runtime-results/handoff/rescue_build_readiness_gate.json` |

## API (`POST`, Prefix `/api/deploy`)

- `/rescue/live-os-base-decision`
- `/rescue/component-inventory`
- `/rescue/mvp-scope-gate`
- `/rescue/debian-live-build-plan`
- `/rescue/iso-test-matrix`
- `/rescue/build-readiness-gate`

Body: `{ "explicit_overwrite": true|false }` — ohne `explicit_overwrite` wird ein bestehendes Handoff nicht ueberschrieben.

## Response-Codes

- `DEPLOY_RESCUE_LIVE_OS_BASE_DECISION_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_COMPONENT_INVENTORY_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_MVP_SCOPE_GATE_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_PLAN_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_ISO_TEST_MATRIX_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_BUILD_READINESS_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`

## Version (Hinweis)

Wenn alle Gates **ok/ready** sind, ist ein manueller Bump **1.7.x → 1.8.0** sinnvoll (neuer Rescue-Strang, neue Routen) — **nicht** automatisch in dieser Phase angewendet.
