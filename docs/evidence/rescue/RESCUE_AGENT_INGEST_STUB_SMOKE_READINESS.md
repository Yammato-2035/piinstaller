# Rescue-Agent Report-Ingest — Stub-Smoke Readiness

**Stand:** 2026-06-02  
**Status:** **`blocked_by_release_restore`**

## Erfüllt

| Voraussetzung | Status |
|---------------|--------|
| Fleet-Smoke grün (Session `…164249`) | **yes** |
| Script Root Cause resolved (`55b7bce` in `/opt`) | **yes** |
| DCC-Port-Mapping dokumentiert | **yes** |
| API Port 8000 erreichbar | **yes** |

## Blockiert

| Voraussetzung | Status |
|---------------|--------|
| `install_profile=release` | **no** — noch `local_lab` |
| Release-Restore belegt | **no** — `release_restore_blocked_sudo_required` |
| `profile_gate_status` unter release verifiziert | **nicht geprüft** |

## Ingest unter release

Rescue-Agent-Router: **`disabled_by_profile`** (erwartbar nach Restore). Stub-Ingest-Smoke erfordert später **gesonderte** `local_lab`-Aktivierung nur für den Ingest-Lauf — nicht in diesem Restore-Lauf.

## Nächster Schritt

1. Operator: Release-Restore (Handoff `FLEET_FINISH_EXIT1_RELEASE_PROFILE_HANDOFF.md`).
2. Post-Restore-Gates dokumentieren.
3. Dann Freigabe: `ready_for_rescue_agent_ingest_stub_smoke` (mit gezieltem `local_lab` nur für Ingest, falls Contract es verlangt).

**Kein Ingest-Smoke in diesem Lauf ausgeführt.**
