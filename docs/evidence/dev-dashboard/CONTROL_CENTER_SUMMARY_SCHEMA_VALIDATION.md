# Control Center Summary — Schema Validation

**Date:** 2026-05-31  
**Branch:** main  
**HEAD:** 8aebf99  
**Runtime version:** 1.7.3.0  

## Entscheidung

**Fall A — Smoke-Kommando war falsch.** Keine Backend-Codeänderung nötig.

Die API liefert ein HTTP-Wrapper-Objekt `{ status, summary }`. Die Sektionen liegen unter `.summary.*`, nicht auf Top-Level.

## HTTP

| Check | Result |
|-------|--------|
| `GET /api/dev-dashboard/control-center-summary` | **HTTP 200** |
| Top-Level-Keys | `status`, `summary` |
| `.runtime` (Top-Level) | `null` — erwartet, Wrapper-Schema |
| `.summary.runtime` | vorhanden, `status=available` |
| `.summary.roadmap` | vorhanden, `status=available` |
| `.summary.dev_server` | vorhanden, `status=available` |

## Kanonische JSON-Pfade

| Sektion | Pfad |
|---------|------|
| runtime | `.summary.runtime` |
| roadmap | `.summary.roadmap` |
| dev_server | `.summary.dev_server` |
| rescue_developer | `.summary.rescue_developer` |
| documentation | `.summary.documentation` |
| diagnostics | `.summary.diagnostics` |
| evidence | `.summary.evidence` |
| next_prompts | `.summary.next_prompts` |
| warnings | `.summary.warnings` |
| errors | `.summary.errors` |

## Summary-Sektionen (`.summary | keys`)

```
dev_server, diagnostics, documentation, errors, evidence, generated_at,
next_prompts, rescue_developer, roadmap, runtime, warnings
```

Alle erwarteten Sektionen vorhanden.

## Konsistenz Backend / Frontend / Tests

| Layer | Erwartung | Status |
|-------|-----------|--------|
| `build_control_center_summary()` | Top-Level-Sektionen (intern) | OK |
| `app.py` Router | `{ status: "success", summary: body }` | OK |
| `frontend/src/api/devDashboardApi.ts` | `data?.summary` | OK |
| Backend-Tests | testen Builder direkt (ohne HTTP-Wrapper) | OK |
| Evidence/Doku | `.summary`-Pfad dokumentiert | OK (korrigiert) |

## Korrekter Smoke-Befehl

```bash
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary \
  | jq '.summary | keys'

curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary \
  | jq '.summary.runtime, .summary.roadmap, .summary.dev_server'
```

**Falsch (liefert null/null/null):**

```bash
jq '.runtime, .roadmap, .dev_server'
```

## Runtime-Gates (gleicher Lauf)

| Gate | Result |
|------|--------|
| `check-runtime-deploy-gate.sh` | OK |
| `check-backend-version-gate.sh` | OK |
| `/api/version` | project_version=1.7.3.0 |
| Dev-Server health | enabled=true, storage_ok=true |

## Status

| Area | Status |
|------|--------|
| Summary-Schema geklärt | **GREEN** |
| Summary-Inhalt vollständig | **GREEN** |
| Backend-Fix nötig | **NEIN** |
