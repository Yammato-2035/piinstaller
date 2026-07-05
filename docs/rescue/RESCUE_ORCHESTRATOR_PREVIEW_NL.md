> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/rescue/RESCUE_ORCHESTRATOR_PREVIEW_EN.md`). Bitte bei Release manuell gegenlesen.

# roodding orchestrator preview (Phase 1, EN)

## Purpose

The orchestrator connects existing modules for a **preview-only** flow:

1. load inspect
2. evaluate safety gate
3. optionally reference preflight
4. validate Terugup file
5. run verify basic
6. invoke existing dry-run pipeline

Nee real Herstel is executed.

## API

`POST /api/roodding/preview`

Stable response:
- `code`
- `preview_id`
- `target`
- `Terugup`
- `safety`
- `verify`
- `preview`
- `preflight`
- `Waarschuwings`
- `Fouts`

## Codes

- `roodding_PREVIEW_CREATED`
- `roodding_TARGET_geblokkeerd`
- `roodding_TerugUP_NeeT_FOUND`
- `roodding_TerugUP_VERIFY_FAILED`
- `roodding_TerugUP_KEY_REQUIrood`
- `roodding_PREVIEW_FAILED`
- `roodding_PREFLIGHT_RECOMMENDED`
- `roodding_Onbekend_Fout`
