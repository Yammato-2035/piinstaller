# Next Prompt Selection

**Stand:** 2026-06-05
**Gewählt:** `RESCUE_TELEMETRY_INGEST_OPERATOR_SMOKE`

## Abgeschlossen

`RESCUE_TELEMETRY_INGEST_SEPARATE_FROM_DCC` — separater Vertrag `/api/rescue/telemetry/*`, nicht `PROFILE_ROUTE_BLOCKED`, Unit-/HTTP-Tests grün im Workspace.

## Nächster Prompt

### `RESCUE_TELEMETRY_INGEST_OPERATOR_SMOKE`

Operator setzt am produktiven/lokalen Backend (mit Freigabe):

```bash
export RESCUE_TELEMETRY_INGEST_ENABLED=1
export RESCUE_TELEMETRY_INGEST_TOKEN='<operator-secret>'
curl -sS http://127.0.0.1:8000/api/rescue/telemetry/health | jq .
# POST mit Sample-Envelope laut WINDOWS_RESCUE_TELEMETRY_SERVER_CONTRACT.md
```

Ohne Backend-Restart bleibt Live-Smoke **gelb** (Ingest disabled in laufender Runtime).

## Parallel P0 (weiter blockiert)

`RESCUE_ISO_UEFI_X64_FAILURE_TRIAGE` — kanonische ISO UEFI-Validator Exit 34, Operator-Rebuild ausstehend.

## Verboten ohne Freigabe

Backend-Restart, USB-Schreiben, Windows-Hardware-Inspect am Zielgerät.
