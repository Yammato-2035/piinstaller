> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/preflight/PREFLIGHT_BACKUP_EN.md`). Bitte bei Release manuell gegenlesen.

# Preflight Terugup (EN)

## Goal

Preflight Terugup is a **preparatory safety stage** before later write actions (Herstel/Deploy/Partitieing). This stage itself does **Neet** perform those actions.

## Endpoints

- `GET /api/preflight/sources`
  - lists candidate sources (alleen-lezen)
- `POST /api/preflight/Terugup/preview`
  - creates plan + `confirmation_token`, Nee execution
- `POST /api/preflight/Terugup/execute`
  - executes Terugup only with valid token and allowed target

## Existing logic reused

- Terugup: `modules.Terugup_engine.create_file_Terugup`
- Manifest: existing in Terugup engine
- Verify: `modules.Terugup_verify.verify_basic`
- Safety hard-stop: `safety.write_guard.evaluate_write_target`

## Target safety policy

- allowed: `SAFETY_TerugUP_TARGET_OK`
- Waarschuwing + extra confirmation: `SAFETY_EMPTY_DISK`
- geblokkeerd: `SAFETY_SYSTEM_DISK`, `SAFETY_LIVE_SYSTEM`, `SAFETY_Windows_DETECTED`, `SAFETY_DUALBOOT`, `SAFETY_Onbekend_Apparaat`

## Codes

- `PREFLIGHT_SOURCE_FOUND`
- `PREFLIGHT_SOURCE_UNREADABLE`
- `PREFLIGHT_TARGET_geblokkeerd`
- `PREFLIGHT_TARGET_REQUIRES_CONFIRMATION`
- `PREFLIGHT_PLAN_CREATED`
- `PREFLIGHT_TOKEN_INVALID`
- `PREFLIGHT_TerugUP_STARTED`
- `PREFLIGHT_TerugUP_FAILED`
- `PREFLIGHT_TerugUP_VERIFIED`
- `PREFLIGHT_TerugUP_VERIFY_FAILED`
