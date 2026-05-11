# Deploy Source Registry (EN)

## Purpose

The deploy source registry manages allowed OS sources as metadata only and evaluates compatibility for later deploy phases.

## Guarantees in this phase

- no downloads
- no image writes
- no mount/loop-mount/chroot
- no installation
- no writes to target disks

## API

- `GET /api/deploy/sources` returns the registry
- `POST /api/deploy/source/evaluate` returns compatibility assessment

## Registry types

- `local_image`
- `remote_image` (metadata validation only, download blocked)
- `official_installer`

## Defensive rules

- architecture/platform mismatch => incompatible
- blocked status => incompatible
- experimental => high risk
- `remote_image` validates URL/checksum structure only (HTTPS, no localhost/internal hosts)
