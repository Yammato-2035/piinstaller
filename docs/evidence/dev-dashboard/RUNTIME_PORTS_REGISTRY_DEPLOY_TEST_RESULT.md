# Runtime Ports Registry — Deploy Test Result

**Datum:** 2026-06-03

## Ergebnisse

| Suite | Ergebnis |
|-------|----------|
| Bash `-n` (healthcheck, QEMU smoke scripts) | **ok** |
| Backend pytest (`runtime_ports` / `backend_health` / `dev_dashboard` / `version`) | **partial** — weder `/opt`-venv noch System-Python haben `pytest` installiert |
| Frontend `npm run build` | **ok** |
| Frontend `npm run test -- --run` | **ok** (54 passed) |

## Status

**partial** — Live-Ingest und Frontend-Tests grün; Backend-Unit-Tests in dieser Session nicht ausführbar (fehlendes pytest). Workspace-Code und `/opt`-Runtime stimmen per API/Watchdog überein.
