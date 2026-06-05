# KB — DCC, Profil und Port-Fehler

## Ports (verbindlich)

| Rolle | Adresse |
|-------|---------|
| Backend/API | `127.0.0.1:8000` |
| UI/DCC | `127.0.0.1:3001` |
| DCC URL | `http://127.0.0.1:3001/?window=cockpit` |
| nginx/default | `127.0.0.1:8080` — **nicht** DCC |

## `Development Control nicht verfügbar` / `profile=release`

**Klassifikation:** `expected_release_profile_block`

| Prüfung | Erwartung unter release |
|---------|-------------------------|
| `/api/version` | HTTP 200 |
| `dev_control_enabled` | `false` |
| Dev-Routen | `404` `PROFILE_ROUTE_BLOCKED` |
| DCC funktional | **nein** — erwarteter Sicherheitszustand |

**Kein** Portfehler. **Kein** Backend-down (wenn `:8000` antwortet).

**DCC gilt erst grün** nach `local_lab` Live-Acceptance (HTTP 200 auf Dev-Routen, Cockpit erreichbar, release danach restored).

Evidence: `DCC_LIVE_ACCEPTANCE_RELEASE_BASELINE.md`, `dcc_live_acceptance_latest.json`

## Portverwechslung

**Klassifikation:** `known_operator_port_confusion`

Symptom: DCC oder API über `:8080` erwartet.  
`:8080` = nginx/Ubuntu-Default, nicht SetupHelfer-DCC.

## Frontend Profile Desync (Build-Time-Gating)

**Klassifikation:** `frontend_gating_build_time_desync`

Symptom: Disabled-Page „profile=release“ im Browser, obwohl `/api/dev-dashboard/status` HTTP 200 liefert (local_lab).

Ursache (historisch): `ExternalDevelopmentControlCenter.tsx` nutzte Build-Time-Marker `devControlUiEnabled` statt Statusroute.

Fix (Workspace `4fb72ee`): `decideDccVisibility()` — Source-of-truth `/api/dev-dashboard/status`; `cache: no-store`; Retry nur Refetch.

| Stufe | Status |
|-------|--------|
| Code-Fix | committed (`4fb72ee`) |
| Deploy `/opt` | **erledigt** (`199d3c6` Fail-safe + Gating) |
| local_lab Browser-Smoke | **partial_green** — Operator: DCC + Diagnose sichtbar; API Status 200 |
| DCC voll grün | **ja** — local_lab + release restore live belegt (`DCC_RELEASE_RESTORE_AFTER_FALLBACK_OPERATOR_OBSERVATION.md`) |

Evidence: `DCC_FRONTEND_PROFILE_DESYNC_RESULT.md`, `DCC_FRONTEND_PROFILE_DESYNC_LIVE_ACCEPTANCE_RESULT.md`

## Fix nicht committed / nicht deployed / nicht live geprüft

**Klassifikation:** `fix_lifecycle_incomplete`

Früherer Lauf: Fix im Workspace, `HEAD` unverändert (`5efff70`), kein belastbarer Abschluss.

Aktuell: Commit nachgeholt; Deploy und local_lab Live-Acceptance blockiert an Operator-`sudo`.

## `local_lab` Live-Smoke blockiert

**Status:** `dcc_profile_switch_blocked` wenn sudo in Agent-Session fehlt.  
**Kein Fake-Green** für DCC.

Operator-Handoff: `DCC_LIVE_ACCEPTANCE_LOCAL_LAB_RESULT.md`, `DCC_FRONTEND_PROFILE_DESYNC_LIVE_ACCEPTANCE_RESULT.md`

## Blank DCC Screen (leerer Browser)

**Klassifikation:** `blank_dcc_screen`

Symptom: `http://127.0.0.1:3001/?window=cockpit` lädt (HTTP 200), aber kein nutzbarer Inhalt — weder DCC noch klare Fehlermeldung.

| Ursache | Klassifikation |
|---------|----------------|
| Altes Bundle ohne Diagnose-Marker | `stale_or_wrong_frontend_bundle` |
| release + Status 404 | `expected_release_profile_block` (Disabled-Page + Diagnose erwartet) |
| React-Renderfehler | `frontend_runtime_error` (ErrorBoundary) |
| API nicht erreichbar | `api_unreachable` |
| Unklassifiziert | `unknown_dcc_boot_failure` (Fallback-Panel) |

**Regel:** DCC darf **nie** leer bleiben. `blank_dcc_screen_unresolved` blockiert Monolith-Aufteilung.

Fix: `DccBootDiagnosticsPanel` + `DccErrorBoundary` + `dccBootState` (Marker `DCC_BOOT_DIAGNOSTICS_V1`).

**Stand 2026-06-05 (deployed bundle + release restore):** `blank_dcc_screen` **resolved** — local_lab DCC sichtbar; release: Disabled-Page + Diagnosepanel, nicht leer. Track **beendet**.

Evidence: `DCC_BLANK_SCREEN_TRIAGE_RESULT.md`, `DCC_RELEASE_RESTORE_AFTER_FALLBACK_OPERATOR_OBSERVATION.md`

## Release-Profilblock erwartet

**Klassifikation:** `release_profile_block_expected` — **confirmed**

| Regel | Inhalt |
|-------|--------|
| release blockiert Dev-Routen | HTTP 404 `PROFILE_ROUTE_BLOCKED` |
| Kein Backend-down | `:8000` antwortet |
| Kein Portfehler | DCC `:3001`, nginx `:8080` nicht DCC |
| UI unter release | Disabled-Page + Boot-Diagnose, **nicht leer** |

## Falsche Next-Prompt-Auswahl

**Klassifikation:** `wrong_next_prompt_selection`

Ursache: `DEV_DASHBOARD_CONTROLLED_COMMAND_RUNS_MVP` als `next_prompt_id` obwohl `reason_de` in `setuphelfer_next_prompts.json` explizit „nicht recommended_next“ (Rescue-Chroot-Cleanup Vorrang) sagt.

Pflicht: Selection-Logik darf Prompts mit `deferred` / niedrigerer Priorität nicht wählen, solange DCC-/Runtime-/Rescue-Blocker aktiv sind.

**Stand:** `fixed_or_mitigated` — `RUNTIME_GOVERNANCE_LIVE_VALIDATION` ist nächster Prompt; Controlled Command Runner forbidden.
