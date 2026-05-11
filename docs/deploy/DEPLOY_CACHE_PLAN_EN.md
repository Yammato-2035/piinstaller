# Deploy Download/Cache Plan (EN)

## Goal

This phase only plans how an OS image could later be safely obtained and locally cached.
No downloads are executed and no data is written.

## Guarantees

- no download
- no network access
- no hash computation
- no extract/mount/chroot
- no writes to target disks

## API

`POST /api/deploy/cache/plan`

Response includes:

- `plan_status`
- `cache.cache_targets` (candidates only, no creation)
- `verification` (expected parameters only)
- `required_steps` (advisory, `auto_allowed=false`)
- `blocked_steps`, `risks`, `warnings`, `errors`
