# KB — Bekannte wiederkehrende Fehler

Kurzreferenz für Knowledge-Base-First-Triage. Details in verlinkter Evidence.

## Klassifikationen

| ID | Symptom | Klassifikation | Nicht verwechseln mit |
|----|---------|----------------|------------------------|
| `expected_release_profile_block` | DCC/Dev-Routen unter `release` | Erwarteter Sicherheitszustand | Portfehler, Backend-down |
| `known_operator_port_confusion` | DCC über `:8080` erwartet | Operator-Portverwechslung | Profilblock |
| `agent_send_failed` | QEMU-Gast sendet keinen Report | Mehrstufig — siehe Rescue-QEMU-KB | Einzelursache ohne Historie |
| `guest_rescue_venv_glibc_mismatch` | `GLIBC_2.38 not found` im Gast-venv | Host-venv in Bookworm-Live | Import/Host-Header |
| `known_error_fix_not_in_artifact` | Fix im Workspace, altes ISO/Squashfs | Artefakt nicht rebuilt | Deploy-only-Fix |
| `frontend_gating_build_time_desync` | DCC Disabled-Page trotz Statusroute 200 | Stale Build-Time-Marker / Cache | `expected_release_profile_block` |
| `fix_lifecycle_incomplete` | Fix „umgesetzt“, aber HEAD/Deploy/Smoke fehlen | Uncommitted oder nicht nach `/opt` | Fake-Green |

## Pflicht vor neuem Fix

1. Frühere Evidence suchen (`docs/evidence/`, diese KB, `RESCUE_QEMU_RECURRENT_FAILURES.md`).
2. Prüfen: deployed? im Artefakt? richtiges Profil? E2E belegt?
3. Gleichen fehlgeschlagenen Lösungsweg nicht wiederholen.

## Verweise

- `docs/knowledge-base/recovery/RESCUE_QEMU_RECURRENT_FAILURES.md`
- `docs/knowledge-base/dev-dashboard/DCC_PROFILE_AND_PORT_ERRORS.md`
- `docs/diagnostics/KNOWN_ERROR_TRIAGE_TEMPLATE.md`
