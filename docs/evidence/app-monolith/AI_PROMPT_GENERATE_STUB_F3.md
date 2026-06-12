# AI Prompt Generate Stub — Phase F.3

**Route:** `POST /api/ai/prompt/generate`  
**Handler:** `ai_prompt_generate_stub` in `backend/app.py`  
**HEAD:** `8bb910c`

## Ist-Zustand

```text
ai_prompt_generate_stub
  → dev_dashboard_core.build_dashboard_status(running_jobs=[], package_activity=[])
  → build_prompt_findings(repo, dash)
  → build_cursor_meta_prompt(repo, findings)
```

## Warum `build_dashboard_status`?

- Stub baut denselben Cockpit-Kontext wie `GET /api/dev-dashboard/cursor-meta-prompt`.
- F.2 migrierte nur den **GET**-Handler; POST-Stub blieb unberührt.
- Kein externer KI-Call (`executed: False`) — reine Prompt-Vorschau.

## Facade-Optionen

| Option | Machbarkeit | Risiko |
|--------|-------------|--------|
| `build_dcc_cursor_meta_prompt_api()` | **hoch** | niedrig — identische Semantik wie GET |
| `build_dashboard_status_body()` + Cockpit | mittel | niedrig |
| Eigene Prompt Context Facade | niedrig | Over-Engineering für einen Stub |

## Bewertung

**Empfehlung: `migrate_to_dcc_status_facade`**

- Einzeiler-Migration: `meta = build_dcc_cursor_meta_prompt_api()` und `prompt` aus `meta`.
- Keine API-/Response-Änderung.
- Kein neues Modul nötig.

## Risiken

| Risiko | Stufe | Mitigation |
|--------|-------|------------|
| Response-Shape-Drift | niedrig | gleiche Facade-Funktion wie GET |
| Profil-Gate | keine | Stub hat kein DCC-Profil-Gate (wie bisher) |
| Performance | niedrig | synchron, wie GET |

**Nicht `unsafe`.** Geplant als **F.4** (kleinster Migrationsschritt).
