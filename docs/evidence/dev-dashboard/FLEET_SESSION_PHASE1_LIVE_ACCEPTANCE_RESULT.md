# Fleet Session Phase 1 - Live Runtime Acceptance Result

**Datum:** 2026-06-02  
**HEAD vorher:** `5bb72c8`  
**HEAD nach Abschluss:** `5bb72c8`  
**Branch:** `main`  
**Repository visibility:** `PUBLIC` (`Yammato-2035/piinstaller`)  
**Push allowed:** no  
**Push durchgeführt:** no  
**NDA risk:** `blocked_public_repository_ndA_risk`

## Ergebnisstatus

**Finaler Status:** `fleet_phase1_live_acceptance_passed`

Die Live-Abnahme wurde nach interaktivem Operator-`sudo` erfolgreich abgeschlossen: `local_lab` war aktiv, die Fleet-API war live erreichbar, genau ein manueller Fleet-Session-Smoke wurde ausgeführt, die Semantiken `timeout`/`serial_empty`/`guest_report_missing` sind live sichtbar, und die Runtime wurde danach wieder auf `release` mit grünem Profile-Gate zurückgestellt.

## Phase-0 Baseline (vor Umschaltung)

- `git branch --show-current`: `main`
- `git rev-parse --short HEAD`: `5bb72c8`
- `gh repo view --json visibility,nameWithOwner`: `PUBLIC`
- `/api/version` vor Abnahme: `install_profile=release`, `fleet_sessions_enabled=false`, `profile_gate_status=green`, `backend_runtime_path=/opt/setuphelfer/backend`
- `./scripts/check-runtime-profile-deploy-gate.sh`: **OK**
- `./scripts/check-runtime-deploy-gate.sh`: **legacy informational** (`LEGACY_GATE_NON_PROFILE_AWARE`)

## Phase-1 local_lab Aktivierung

Operator hat interaktiv ausgeführt:

- `sudo cp packaging/systemd/dropins/92-install-profile-local-lab.conf.example /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf`
- `sudo systemctl daemon-reload`
- `sudo systemctl restart setuphelfer-backend.service`

Nachweis:

- `/api/version`: `install_profile=local_lab`
- `fleet_sessions_enabled=true`
- `public_exposure_allowed=false`
- `./scripts/check-runtime-profile-deploy-gate.sh`: **OK**

## Phase-2 Fleet API Live-Sichtbarkeit

OpenAPI-Pfade live vorhanden:

- `/api/fleet/sessions`
- `/api/fleet/sessions/summary`
- `/api/fleet/sessions/{session_id}`
- `/api/fleet/sessions/{session_id}/heartbeat`
- `/api/fleet/sessions/{session_id}/finish`

HTTP-Sonden:

- `GET /api/fleet/sessions` -> `HTTP 200`
- `GET /api/fleet/sessions/summary` -> `HTTP 200`

## Phase-3 Genau ein manueller Fleet-Session-Smoke (ohne QEMU)

- `RUN_ID=manual_fleet_phase1_acceptance_20260602_125333`
- `SESSION_ID=fleet-manual_fleet_phase1_acceptance_20260602_125333`
- Serial-Datei angelegt als leer (`size_bytes=0`)

Create:

- Ergebnis: **OK** (`FLEET_SESSION_CREATED`)
- Session direkt sichtbar (`FLEET_SESSION_OK`)
- `guest.report_seen=false`
- `guest.dev_server_report_new=false`
- `guest.guest_node_id=null`
- `serial.size_bytes=0`
- Findings: `serial_empty`, `guest_report_missing`

Heartbeat:

- Endpoint aufgerufen.
- Ergebnis: **blocked invalid payload** (`invalid_status`) wegen `status=running` (nicht in erlaubten Fleet-Statuswerten).
- Bewertung: für Abnahme **nicht kritisch**, da Create + Finish + Final Read + Persistenz vollständig erfolgreich waren.

Finish:

- Ergebnis: **OK** (`FLEET_SESSION_FINISHED`)
- `status=timeout`
- `severity=error`
- `qemu.exit_code=124`
- `serial.size_bytes=0`
- Findings enthalten: `qemu_timeout_124`, `serial_empty`, `guest_report_missing`
- `guest.report_seen=false`
- `guest.dev_server_report_new=false`
- kein `guest_node_id`

Final Read / Summary / List:

- Session final als `timeout` sichtbar.
- Session erscheint in der Liste vor Guest-Ingest.
- Kein neuer Gast-Knoten erzeugt.
- Keine Fake-VM erzeugt.

## Phase-4 Persistenz

Persistenzpfad der Live-Runtime (`/opt`) verifiziert:

- `/opt/setuphelfer/docs/evidence/runtime-results/dev-dashboard/fleet_sessions.jsonl`
- `/opt/setuphelfer/docs/evidence/runtime-results/dev-dashboard/fleet_sessions_latest.json`

`RUN_ID` ist in `latest` und `jsonl` nachweisbar (finaler Eintrag mit `timeout`, `exit_code=124`, Findings wie oben). Keine Secrets und keine Fake-Gastdaten festgestellt.

## Phase-5 UI Source / Dist

- UI-Source geprüft: **yes**
  - `LabSessionsPanel`, `serial_empty`, `guest_report_missing`, Host-Session-Hinweise vorhanden.
- UI-dist geprüft: **unknown** (kein erzwungener Rebuild, keine Matches im vorhandenen `dist`).

## Phase-6 Release wiederhergestellt

Operator hat interaktiv ausgeführt:

- `sudo cp packaging/systemd/dropins/92-install-profile-release.conf.example /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf`
- `sudo systemctl daemon-reload`
- `sudo systemctl restart setuphelfer-backend.service`

Nachweis:

- `/api/version`: `install_profile=release`, `profile_gate_status=green`, `fleet_sessions_enabled=false`
- `./scripts/check-runtime-profile-deploy-gate.sh`: **OK**
- Release-Probes:
  - `GET /api/fleet/sessions` -> `HTTP 404` (`PROFILE_ROUTE_BLOCKED`)
  - `GET /api/fleet/sessions/summary` -> `HTTP 404` (`PROFILE_ROUTE_BLOCKED`)

## Phase-7 Tests (nach Abschluss)

- `pytest tests/test_fleet_session_state_v1.py tests/test_fleet_session_api_v1.py -q` -> **14 passed**
- `bash -n scripts/rescue-live/run-qemu-developer-iso-smoke.sh` -> **OK**
- `bash -n scripts/rescue-live/fleet-session-api.sh` -> **OK**
- `npm run typecheck`: `frontend_typecheck_missing_script` (nicht als Test-Fail gewertet)

## Pflichtfelder (Live-Abnahme-Matrix)

| Feld | Wert |
|------|------|
| Runtime-Profil vor Abnahme | `release` |
| local_lab aktiviert | yes |
| local_lab profile gate exit | OK |
| Fleet API live sichtbar | yes |
| RUN_ID | `manual_fleet_phase1_acceptance_20260602_125333` |
| SESSION_ID | `fleet-manual_fleet_phase1_acceptance_20260602_125333` |
| Create Ergebnis | OK |
| Heartbeat Ergebnis | blocked (`invalid_status`) |
| Finish Ergebnis | OK |
| Final Session status | `timeout` |
| qemu.exit_code | `124` |
| serial.size_bytes | `0` |
| serial_empty sichtbar | yes |
| guest_report_missing sichtbar | yes |
| qemu_timeout_124 sichtbar | yes |
| Session vor Guest-Ingest sichtbar | yes |
| Gast-Knoten erzeugt | no |
| Fake-VM erzeugt | no |
| Persistenz geprüft | yes (`/opt/setuphelfer/.../fleet_sessions*.json*`) |
| UI Source geprüft | yes |
| UI dist geprüft | unknown |
| release wiederhergestellt | yes |
| finales Runtime-Profil | `release` |
| Kein QEMU-Lauf | yes |
| Kein ISO-Build | yes |
| Kein USB/dd | yes |
| Kein Backup | yes |
| Kein Restore | yes |
| Kein apt install/upgrade | yes |
| Kein Push | yes |

## Offene Risiken

- Heartbeat-Payload verwendet `status=running`, was im aktuellen Statusvertrag ungültig ist (`invalid_status`).
- Empfehlung: Wrapper/Smoke-Helper auf erlaubten Statuswert (`starting`, `booting`, `serial_active`, ...) anpassen oder Heartbeat ohne `status` senden.

## Nächster sinnvoller Schritt

1. Heartbeat-Payload im Wrapper an erlaubte Statuswerte anpassen.  
2. Danach optional ein kurzer API-only Regressionstest für den Heartbeat-Pfad (ohne QEMU) hinzufügen.  
3. Push bleibt weiterhin blockiert (`PUBLIC` + NDA-Risiko).

## Nachtrag (statisch, ohne Runtime-Smoke)

- Wrapper passt `status=running` auf `agent_state=alive` an.
- Backend-Heartbeat akzeptiert Contract ohne ungültige Status-Überschreibung.
- Live-Runtime wurde in diesem Nachtrag nicht erneut gegen Port 8000 getestet (`runtime_gate_blocked_static_analysis_only`).
