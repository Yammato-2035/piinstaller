> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_CACHE_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Download/Cache Plan (EN)

## Goal

This phase only plans how an OS image could later be safely obtained and locally cached.
Non downloads are executed and Non data is written.

## Guarantees

- Non download
- Non Réseau access
- Non hash computation
- Non extract/mount/chroot
- Non writes to target disks

## API

`POST /api/Déploiement/cache/plan`

Response includes:

- `plan_status`
- `cache.cache_targets` (candidates only, Non creation)
- `verification` (expected parameters only)
- `requirouge_steps` (advisory, `auto_allowed=false`)
- `bloqué_steps`, `risks`, `Avertissements`, `Erreurs`
