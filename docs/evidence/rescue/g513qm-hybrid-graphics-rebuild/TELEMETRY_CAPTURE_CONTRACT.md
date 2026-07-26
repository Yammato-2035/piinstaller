# Telemetry / capture contract (G513QM)

## Principles

- Local Evidence on SETUP_LOGS is primary.
- Telemetry server is secondary.
- Boot success must not depend on network/telemetry.
- Runtime gate currently blocks claiming live API telemetry send (workspace vs API version drift).

## Upload status vocabulary

`not_configured` | `consent_missing` | `queued_offline` | `uploading` | `accepted` | `rejected` | `failed_retryable` | `failed_terminal`

`queued_offline` ≠ `accepted`.

## Redaction before upload

MAC, IP (non-essential), SSID, usernames, hostnames, serials, UUIDs/EUI/NGUID, secrets/tokens/passwords, user home paths.

## Preferred path

Rescue stick → Telemetry server → Diagnostikserver (no direct unvalidated diagnostik APIs from stick in this rebuild).

## Capture autostart

`setuphelfer_capture=1` on G513QM profiles; scripts:

- `scripts/setuphelfer-g513qm-capture.sh`
- modes in `install-from-rescue.sh` (`capture-only`, `finalize-capture`)
