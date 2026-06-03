# QEMU Guest Agent After Registry — Ingest Test Result

**Datum:** 2026-06-03

| Suite | Ergebnis |
|-------|----------|
| `bash -n` healthcheck + QEMU scripts | **ok** |
| Backend pytest (`runtime_ports` / `fleet` / `rescue_agent` / `backend_health`) | **partial** — `pytest` nicht installiert (System-/opt-venv) |

## Status

**partial** — Statische Skript-Checks OK; keine Backend-Unit-Tests in dieser Session.
