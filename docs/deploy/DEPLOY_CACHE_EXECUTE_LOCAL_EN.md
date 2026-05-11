# Deploy Cache Execute – Local-only (EN)

## Goal

This phase only copies local image files into Setuphelfer cache or marks them as already ready.

## Safety boundaries

- no network access
- no remote download
- no mount/extract/chroot
- no writes to target disks
- no installation

## API

- `POST /api/deploy/cache/session`
- `POST /api/deploy/cache/execute`

## Flow

1. validate session + token + TTL
2. validate source hash against session
3. re-validate local file
4. optional SHA256 check when checksum is provided
5. containment-safe copy to allowed cache path or mark ready

## Notes

- session is single-use
- remote sources are blocked in this phase
