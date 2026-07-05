> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_SOURCE_REGISTRY_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Source Registry (EN)

## Purpose

The Deploy source registry manages allowed OS sources as metadata only and evaluates compatibility for later Deploy phases.

## Guarantees in this phase

- Nee downloads
- Nee image writes
- Nee mount/loop-mount/chroot
- Nee installation
- Nee writes to target disks

## API

- `GET /api/Deploy/sources` returns the registry
- `POST /api/Deploy/source/evaluate` returns compatibility assessment

## Registry types

- `local_image`
- `remote_image` (metadata validation only, download geblokkeerd)
- `official_installer`

## Defensive rules

- architecture/platform mismatch => incompatible
- geblokkeerd status => incompatible
- experimental => high risk
- `remote_image` validates URL/checksum structure only (HTTPS, Nee localhost/Intern hosts)
