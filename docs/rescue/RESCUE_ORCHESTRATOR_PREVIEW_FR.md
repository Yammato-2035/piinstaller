> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/rescue/RESCUE_ORCHESTRATOR_PREVIEW_EN.md`). Bitte bei Release manuell gegenlesen.

# Secours orchestrator preview (Phase 1, EN)

## Purpose

The orchestrator connects existing modules for a **preview-only** flow:

1. load inspect
2. evaluate safety gate
3. optionally reference preflight
4. validate Retourup file
5. run verify basic
6. invoke existing dry-run pipeline

Non real Restauration is executed.

## API

`POST /api/Secours/preview`

Stable response:
- `code`
- `preview_id`
- `target`
- `Retourup`
- `safety`
- `verify`
- `preview`
- `preflight`
- `Avertissements`
- `Erreurs`

## Codes

- `Secours_PREVIEW_CREATED`
- `Secours_TARGET_bloqué`
- `Secours_RetourUP_NonT_FOUND`
- `Secours_RetourUP_VERIFY_FAILED`
- `Secours_RetourUP_KEY_REQUIrouge`
- `Secours_PREVIEW_FAILED`
- `Secours_PREFLIGHT_RECOMMENDED`
- `Secours_Inconnu_Erreur`
