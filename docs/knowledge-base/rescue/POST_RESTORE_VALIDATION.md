# Rescue Post-Restore Validation

## Why this exists
Restore success at engine level does not guarantee a plausible target structure.
Post-Restore Validation adds a defensive, read-only quality gate after restore.

## What it does
- Validates basic Linux target structure (`/etc`, `/usr`, `/var`)
- Checks boot artifacts (`/boot`, kernel, initramfs)
- Checks setuphelfer artifacts (systemd unit + install path)
- Produces `valid | warning | failed` and code-based findings

## What it does NOT do
- No boot repair
- No partition changes
- No automatic setuphelfer installation
- No write operations to target system disks

## Operational behavior
- `failed`: target path missing/unreadable or core structure missing
- `warning`: restore may still be usable, but follow-up is recommended
- `valid`: no current findings

## API/Orchestrator outputs
- Rescue Execute now includes `post_verify` in response
- Optional endpoint: `POST /api/rescue/post-restore/validate`
