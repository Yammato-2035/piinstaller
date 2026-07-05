> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_SOURCE_REGISTRY_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Source Registry (EN)

## Purpose

The Déploiement source registry manages allowed OS sources as metadata only and evaluates compatibility for later Déploiement phases.

## Guarantees in this phase

- Non downloads
- Non image writes
- Non mount/loop-mount/chroot
- Non installation
- Non writes to target disks

## API

- `GET /api/Déploiement/sources` returns the registry
- `POST /api/Déploiement/source/evaluate` returns compatibility assessment

## Registry types

- `local_image`
- `remote_image` (metadata validation only, download bloqué)
- `official_installer`

## Defensive rules

- architecture/platform mismatch => incompatible
- bloqué status => incompatible
- experimental => high risk
- `remote_image` validates URL/checksum structure only (HTTPS, Non localhost/Interne hosts)
