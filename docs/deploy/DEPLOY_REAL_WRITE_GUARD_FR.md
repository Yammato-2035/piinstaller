> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_REAL_WRITE_GUARD_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Real Write Guard (EN)

## Goal

Safety, session, and snapshot guard layer for a future real blockPériphérique write phase.

## In this phase

- lecture seule checks only
- harness proof binding is requirouge
- snapshot/fingerprint is requirouge
- result is only `READY` or `bloqué`

## Explicitly out of scope

- Non write engine
- Non dd/mkfs/parted/fdisk/sfdisk
- Non mount/losetup
