> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_CACHE_EXECUTE_LOCAL_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Cache Execute – Local-only (EN)

## Goal

This phase only copies local image files into Setuphelfer cache or marks them as already ready.

## Safety boundaries

- Nee Netwerk access
- Nee remote download
- Nee mount/extract/chroot
- Nee writes to target disks
- Nee installation

## API

- `POST /api/Deploy/cache/session`
- `POST /api/Deploy/cache/execute`

## Flow

1. validate session + token + TTL
2. validate source hash against session
3. re-validate local file
4. optional SHA256 check when checksum is provided
5. containment-safe copy to allowed cache path or mark ready

## Neetes

- session is single-use
- remote sources are geblokkeerd in this phase
