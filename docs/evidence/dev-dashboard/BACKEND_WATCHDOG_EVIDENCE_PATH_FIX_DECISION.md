# Backend Watchdog Evidence Path — Fix Decision

**Datum:** 2026-06-03

## Root Cause

Healthcheck schrieb nach `/opt/setuphelfer/docs/...`, aber die Datei war **nur für Owner lesbar (600)**. Der API-Prozess (`setuphelfer`) konnte sie nicht lesen und meldete fälschlich „not found“.

## Gewählte Lösung

1. **Skript:** deterministisches `REPO_ROOT` (ENV oder `BASH_SOURCE`); optional `SETUPHELFER_HEALTH_EVIDENCE_DIR`; **`chmod 664`** auf JSON/JSONL; Pfad-Metadaten im JSON.
2. **Loader:** geordnete Suche (`/opt` bevorzugt bei Runtime unter `/opt`); `searched_paths`; klare Meldung bei `permission_denied`.
3. **Kein** Shell-Aufruf aus dem Backend; kein Autorestart.

## ENV

| Variable | Wirkung |
|----------|---------|
| `SETUPHELFER_REPO_ROOT` | Repo-Root für Evidence-Pfad |
| `SETUPHELFER_HEALTH_EVIDENCE_DIR` | Überschreibt Evidence-Verzeichnis |

## Sicherheit

Evidence bleibt developer-only; `664` in setgid-Gruppe `setuphelfer` erlaubt nur Gruppen-Lesezugriff, kein world-write.
