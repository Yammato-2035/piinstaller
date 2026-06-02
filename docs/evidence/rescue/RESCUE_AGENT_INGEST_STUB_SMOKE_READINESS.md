# Rescue-Agent Report-Ingest — Stub-Smoke Readiness

**Stand:** 2026-06-02  
**Status:** **`ready_for_rescue_agent_ingest_stub_smoke`**

## Voraussetzungen

| Kriterium | Status |
|-----------|--------|
| `release_restore_status=ok` | **yes** |
| Fleet-Smoke green | **yes** (Session `…164249`) |
| DCC-Port-Mapping green | **yes** |
| `profile_gate_status=green` | **yes** |
| Runtime-Code-Drift nicht rot | **yes** (`runtime_code_drift_yellow`) |
| Rescue-Agent-Router unter `release` | **`disabled_by_profile`** (5 Router) |
| `55b7bce` in `/opt` | **yes** |

## Ingest-Lauf (noch nicht ausgeführt)

Stub-Ingest-Smoke **nicht** in diesem Lauf gestartet.

Für den Smoke-Lauf: **`local_lab` gesondert aktivieren** (Operator), da Router unter `release` blockiert sind.

## Nächster Schritt

1. Operator: kurz `local_lab` für Ingest-Smoke
2. Report-Ingest Stub Smoke ausführen
3. `release` wiederherstellen

Evidence: `RELEASE_PROFILE_RESTORE_OPERATOR_INGEST.md`, `RUNTIME_DRIFT_CLASSIFICATION_AFTER_RELEASE_RESTORE.md`
