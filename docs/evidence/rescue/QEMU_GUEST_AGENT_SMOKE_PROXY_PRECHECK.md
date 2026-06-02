# QEMU Guest Agent Smoke — Proxy Precheck

**Datum:** 2026-06-02

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Host-API 127.0.0.1:8000 | **yes** (Backend aktiv) |
| Dev-Server/Fleet in `release` | **PROFILE_ROUTE_BLOCKED** (404) |
| Proxy 127.0.0.1:8001 | nicht gestartet (kein QEMU-Lauf) |
| Gast-Endpoint (Projekt) | `http://10.0.2.2:8001` → Host `127.0.0.1:8000` |

## Bewertung

**Status: blocked** — Proxy/Fleet-Ingest erfordert `local_lab`; Agent konnte Profil nicht wechseln.

Operator: `run-qemu-developer-iso-smoke.sh` startet Proxy automatisch bei `--operator-confirm-qemu`.
