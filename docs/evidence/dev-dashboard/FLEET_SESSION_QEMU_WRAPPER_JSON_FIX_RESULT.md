# Fleet Session QEMU Wrapper — JSON Payload Fix Result

**Datum:** 2026-06-01  
**Basis-HEAD:** `8ed0ff5` (vor Fix-Commit)

## NDA / Push

| Feld | Wert |
|------|------|
| Visibility | **public** |
| Push | **no** (`push_blocked_public_repository_ndA_risk`) |

## Alter Lauf `080405`

| Punkt | Wert |
|-------|------|
| QEMU noch aktiv während Analyse | **yes** (nicht gekillt) |
| Fachlich bewertet | **no** (Wrapper-Bug) |
| Session-Status | `timeout_warning`, Heartbeat stale — Telemetrie unvollständig |

## Fix

| Datei | Änderung |
|-------|----------|
| `scripts/rescue-live/fleet-session-api.sh` | `fleet_session_*_payload()`, `fleet_validate_json`, sicherer Fallback |
| `scripts/rescue-live/run-qemu-developer-iso-smoke.sh` | Entfernt `_fleet_serial_patch_json` und alle kaputten `python3 -c` Dict-Builder |
| `scripts/rescue-live/start-qemu-lab-dev-server-proxy.sh` | Default `bind=127.0.0.1`; `0.0.0.0` nur mit `OPERATOR_CONFIRM_LAN_BIND` |
| `scripts/rescue-live/test_fleet_session_shell_payloads_v1.sh` | Payload-Unit-Tests ohne QEMU |

## JSON-Erzeugung (neu)

- Werte nur via **ENV** an Python-Heredoc.
- Booleans als echte Python-`bool` → JSON `true`/`false`.
- Pfade als JSON-Strings, keine manuelle Quote-Kaskade.

## Tests

| Test | Ergebnis |
|------|----------|
| `bash -n` (wrapper, api, proxy) | OK |
| `test_fleet_session_shell_payloads_v1.sh` | OK |
| API `manual_wrapper_payload_smoke_*` create/heartbeat/finish/get/list/summary | OK |
| Kein NameError `true` | OK |
| Serial-Pfad mit `/` korrekt | OK |

## Proxy-Bind

| Modus | Bind | Bewertung |
|-------|------|-----------|
| Manuell `start-qemu-lab-dev-server-proxy.sh` | **127.0.0.1** (Default) | **green** — kein LAN-Bind |
| QEMU-Smoke mit Proxy | **0.0.0.0** + `OPERATOR_CONFIRM_LAN_BIND=true` | **yellow** — slirp/10.0.2.2 erfordert; dokumentiert, nicht öffentlich |

## QEMU next step

`qemu_smoke_next_step_allowed=true` — nach **neuem** Smoke-Lauf (nicht Retry von `080405`).

## Nicht durchgeführt

Kein neuer QEMU-Lauf, kein ISO/USB/Backup/Restore/apt/Push.
