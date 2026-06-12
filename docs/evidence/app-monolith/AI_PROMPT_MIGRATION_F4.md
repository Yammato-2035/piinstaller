# AI Prompt Migration — Phase F.4

**HEAD:** `204ac1c` → F.4 · **Route:** `POST /api/ai/prompt/generate`

## Änderung

| Vorher | Nachher |
|--------|---------|
| `build_dashboard_status()` + Cockpit direkt | `build_dcc_cursor_meta_prompt_api()` |

## Validierung

| Kriterium | Ergebnis |
|-----------|----------|
| Gleiche Datenbasis | ✅ `build_dashboard_status_body` via Facade (wie GET cursor-meta-prompt) |
| Gleiche Antwortstruktur | ✅ `{status, provider, executed, message_key, prompt}` unverändert |
| Fehlerbehandlung | ✅ `invalid_provider`, `confirmation_required` unverändert |
| Neue Promptlogik | ❌ keine |

## Code

`backend/app.py` → `ai_prompt_generate_stub` importiert nur noch `build_dcc_cursor_meta_prompt_api`.
