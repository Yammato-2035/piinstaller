> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_REAL_WRITE_GUARD_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Real Write Guard (EN)

## Goal

Safety, session, and snapshot guard layer for a future real blockApparaat write phase.

## In this phase

- alleen-lezen checks only
- harness proof binding is requirood
- snapshot/fingerprint is requirood
- result is only `READY` or `geblokkeerd`

## Explicitly out of scope

- Nee write engine
- Nee dd/mkfs/parted/fdisk/sfdisk
- Nee mount/losetup
