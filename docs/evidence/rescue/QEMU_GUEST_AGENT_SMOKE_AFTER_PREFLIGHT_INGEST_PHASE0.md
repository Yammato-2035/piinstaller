# QEMU Guest Agent Smoke After Preflight — Ingest Phase 0

**Datum:** 2026-06-03  
**HEAD:** `b5075a5`  
**Branch:** `main`

## Runtime nach Smoke (aktuell)

| Feld | Wert |
|------|------|
| Runtime-Profil | `release` |
| `profile_gate_status` | `green` |
| `dev_control_enabled` | `false` |
| `setuphelfer-backend.service` | active |

## Release-Trap

| Feld | Wert |
|------|------|
| release restored | **yes** (Profil `release`, Dev-Routen `PROFILE_ROUTE_BLOCKED`) |

## QEMU-Evidence

| Feld | Wert |
|------|------|
| QEMU evidence dirs gefunden | **yes** (ältester/neuester mtime: `qemu_rescue_developer_autopilot_20260602_202725`) |
| Post-Preflight-Smoke-Evidence (head `b5075a5`, `DEVSERVER_PREFLIGHT_OK`) | **no** |

## Lauf-Grenzen

| Aussage | Wert |
|---------|------|
| Dieser Lauf startet kein QEMU | **yes** |

## Hinweis

Operator-Auftrag behauptet Smoke nach gehärtetem Preflight und ISO `614cc86e…`. Im Evidence-Baum existiert **kein** Run-Verzeichnis nach `2026-06-03T00:14` (ISO-Ingest). Einziger Operator-Smoke-Log: `20260602_202725` mit `head=9607b63` und `PROFILE_GUARD_OK` (ohne `DEVSERVER_PREFLIGHT_OK`) — **vor** ISO-Rebuild und Preflight-Guard-Commit.
