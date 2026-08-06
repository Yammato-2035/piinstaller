# PHASE 19 – Qualitätsgates — PI-RS-HW-BASELINE-DIAG-I18N-002

Stand: 2026-08-06, Workspace `/home/volker/piinstaller-hw-baseline-diag-i18n-002`,
Branch `pi-rs-hw-baseline-diag-i18n-002`, Basis `dfa9ae18`.

Maschinenlesbar: `PHASE19_QUALITY_GATES.json`.

## Ergebnisüberblick

| Gate | Ergebnis |
|------|----------|
| Runtime-Deploy-Gate | Exit 0 (Legacy/Profil-Hinweis; **kein** Live-`/opt`-Erfolg behauptet) |
| Modul-Boundary-Guard | Exit 0, Status `review_required` (vorbestehend); Baseline-`hardware_new_logic`-Treffer behoben |
| Hardware-Doc-i18n | Exit 0; `structurally_complete` + `content_reviewed`; `native_review_pending: true` |
| Version-Consistency | `ok=True` |
| OpenAPI Baseline | 9 Routen, nur GET/POST-Preview; keine verbotenen Write-Routen |
| Neue Baseline-Suite | **213 passed** |
| Hardware-Testgruppe | **405 passed** (32 Dateien) |
| Rescue-Testgruppe | **702 passed**, 23 skipped (venv mit `httpx`) |
| Telemetrie/API | **55 passed** |
| Frontend-Typecheck | 194 vorbestehende TS-Fehler; **0** in Baseline-Dateien |
| Frontend-Vitest | 2 failed / 172 passed — `rescueStickUsbGate` unverändert vs. Basis |
| Frontend-Build | Vite Exit 0 |
| Vollständige Backend-Suite | **4048 passed**, 9 failed, 29 skipped |

## Vollsuite vs. Vorgängerbaseline (3.450)

Die Compat-001-Baseline zählte **3.450 passed** bei Ausschluss httpx-abhängiger Dateien.
Dieser Lauf nutzte `/home/volker/piinstaller/.venv` (httpx vorhanden) → größere Collection
(**4048 passed**). Delta ist Sammlungsumfang, nicht „weniger Tests“.

## Fehlerschichtung (alle 9 Failures)

Vergleichslauf auf detached `dfa9ae18` reproduziert dieselben persistenten Fehler.
Kein durch diese Phase verursachter Regressionfehler.

- `test_app_router_slice_e8` (2× `11 != 10`) — vorbestehend (hardware-provisioning GET)
- `test_deploy_runner_rescue_storage_discovery_v1` — vorbestehend (`review_required != ok`)
- `test_pi_rs_payload_telemetry001_*` (3) — vorbestehend (Pin/Permissions/+x im Worktree)
- `test_pi_rs_tel003/004_version_bump` (2) — vorbestehend (Pin `1.9.19.5` vs. `1.10.0.0`)
- `test_msi_windows_routes_readonly_v1` — Suite-Flake (Event-Loop); isoliert **5/5 passed** auf Branch und Basis

## Statuskennzeichnung

`phase19_quality_gates_complete_with_preexisting_failures_documented`

Kein Anspruch: `physical_matrix_passed`, `memory_fully_verified`, `production_ready`.
