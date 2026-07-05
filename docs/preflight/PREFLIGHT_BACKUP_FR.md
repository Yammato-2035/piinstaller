> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/preflight/PREFLIGHT_BACKUP_EN.md`). Bitte bei Release manuell gegenlesen.

# Preflight Retourup (EN)

## Goal

Preflight Retourup is a **preparatory safety stage** before later write actions (Restauration/Déploiement/Partitioning). This stage itself does **Nont** perform those actions.

## Endpoints

- `GET /api/preflight/sources`
  - lists candidate sources (lecture seule)
- `POST /api/preflight/Retourup/preview`
  - creates plan + `confirmation_token`, Non execution
- `POST /api/preflight/Retourup/execute`
  - executes Retourup only with valid token and allowed target

## Existing logic reused

- Retourup: `modules.Retourup_engine.create_file_Retourup`
- Manifest: existing in Retourup engine
- Verify: `modules.Retourup_verify.verify_basic`
- Safety hard-stop: `safety.write_guard.evaluate_write_target`

## Target safety policy

- allowed: `SAFETY_RetourUP_TARGET_OK`
- Avertissement + extra confirmation: `SAFETY_EMPTY_DISK`
- bloqué: `SAFETY_SYSTEM_DISK`, `SAFETY_LIVE_SYSTEM`, `SAFETY_Windows_DETECTED`, `SAFETY_DUALBOOT`, `SAFETY_Inconnu_Périphérique`

## Codes

- `PREFLIGHT_SOURCE_FOUND`
- `PREFLIGHT_SOURCE_UNREADABLE`
- `PREFLIGHT_TARGET_bloqué`
- `PREFLIGHT_TARGET_REQUIRES_CONFIRMATION`
- `PREFLIGHT_PLAN_CREATED`
- `PREFLIGHT_TOKEN_INVALID`
- `PREFLIGHT_RetourUP_STARTED`
- `PREFLIGHT_RetourUP_FAILED`
- `PREFLIGHT_RetourUP_VERIFIED`
- `PREFLIGHT_RetourUP_VERIFY_FAILED`
