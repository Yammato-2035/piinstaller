# Rescue Agent Pairing Contract (Stub)

Status: **Contract + API-Stub**, keine produktive Freischaltung.

## Ablauf

1. Agent sendet Pairing-Request mit Boot-Identity + Public Key
2. Dashboard zeigt pending Agent
3. Operator bestätigt
4. Kurzlebige Session wird ausgestellt (`expires_at`)

## Regeln

- Kein dauerhaftes Token im ISO/Image
- Kein hardcodierter API-Key
- Nur `local_lab/dev` oder explizit `rescue_pairing_enabled`
- Revoke/Expire vorgesehen (Folgeschritt)

## Response

- `registration_status`: `pending|accepted|rejected|expired`
- `session_id`, `server_public_key`, `expires_at`, `allowed_scopes`
