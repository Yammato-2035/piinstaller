# Rescue Agent / Fleet — Static Review

**Stand:** 2026-06-02

## Router-Sicherheit

- Prefix `/api/rescue-agent`; nur POST/GET Preview/Register/Heartbeat/Report/Sessions
- Keine `/execute`, `/apply`, `/install`, `/write`-Routen
- `release`/`production`: Registration HTTP 403 (`RESCUE_AGENT_REGISTRATION_DISABLED_IN_RELEASE`)
- In-Memory-Sessions (`_SESSIONS`); kein Persist-Write auf Systempfade

## Profil-Gating

- `install_profile`: `FORBIDDEN_API_PREFIXES_RELEASE` enthält `/api/rescue-agent`
- `should_register_rescue_agent_router()` → `rescue_remote_enabled` (in release typisch false)
- App-Bootstrap: optionaler Router, `disabled_by_profile` / `import_failed` ohne Startabbruch

## E2EE

- Status: **`contract_stub_only`**
- `build_encrypted_envelope` Stub; Klartext-Report nur mit `test_mode_allow_unencrypted`
- Produktive E2EE: **nicht** behauptet

## nftables

- Status: **`preview_only_apply_false`**
- `apply_allowed: false`; nur `commands_preview`

## System Report

- Nutzt Facades (`storage_facade`, `mount_facade`) defensiv
- Fehlende Facade → `review_required` im Report, kein Crash

## Fleet Heartbeat

- `status=running` im Heartbeat wird entfernt; `agent_state=alive` gesetzt
- `agent_state=running` → `FLEET_SESSION_BLOCKED_INVALID_PAYLOAD`
- Session-`status` und `agent_state` getrennt
- `scripts/rescue-live/fleet-session-api.sh` spiegelt Neutralisierung

## No-Write / No-Apply

- Kein `subprocess`, `os.system`, `mount`/`mkfs`/`dd` in `rescue_agent/`
- `secrets.token_hex` nur für Session-IDs (keine committeten Geheimnisse)

## Offene Risiken

- Live-Runtime ohne Deploy: Router/Diagnose nicht sichtbar
- `local_lab` Fleet-Smoke und Rescue-Ingest **ausstehend** (nach Operator-Sync)
