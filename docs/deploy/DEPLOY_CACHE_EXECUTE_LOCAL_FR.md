> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_CACHE_EXECUTE_LOCAL_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Cache Execute – Local-only (EN)

## Goal

This phase only copies local image files into Setuphelfer cache or marks them as already ready.

## Safety boundaries

- Non Réseau access
- Non remote download
- Non mount/extract/chroot
- Non writes to target disks
- Non installation

## API

- `POST /api/Déploiement/cache/session`
- `POST /api/Déploiement/cache/execute`

## Flow

1. validate session + token + TTL
2. validate source hash against session
3. re-validate local file
4. optional SHA256 check when checksum is provided
5. containment-safe copy to allowed cache path or mark ready

## Nontes

- session is single-use
- remote sources are bloqué in this phase
