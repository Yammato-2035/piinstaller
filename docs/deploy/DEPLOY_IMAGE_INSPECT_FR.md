> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_IMAGE_INSPECT_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Image Inspect (EN)

## Goal

lecture seule pre-check of a locally cached image before future Déploiement approval.

## Allowed checks

- file exists
- regular file
- path under allowed Setuphelfer cache
- extension (.img/.iso/.qcow2)
- file size > 0
- optional SHA256 verification when expected_checksum is provided

## Nont allowed

- Non mount/loop-Périphérique
- Non extract
- Non Partition analysis
- Non image content inspection
- Non installation
