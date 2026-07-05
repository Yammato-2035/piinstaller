> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_CACHE_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Download/Cache Plan (EN)

## Goal

This phase only plans how an OS image could later be safely obtained and locally cached.
Nee downloads are executed and Nee data is written.

## Guarantees

- Nee download
- Nee Netwerk access
- Nee hash computation
- Nee extract/mount/chroot
- Nee writes to target disks

## API

`POST /api/Deploy/cache/plan`

Response includes:

- `plan_status`
- `cache.cache_targets` (candidates only, Nee creation)
- `verification` (expected parameters only)
- `requirood_steps` (advisory, `auto_allowed=false`)
- `geblokkeerd_steps`, `risks`, `Waarschuwings`, `Fouts`
