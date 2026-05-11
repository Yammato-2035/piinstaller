# Deploy Real Write Guard (EN)

## Goal

Safety, session, and snapshot guard layer for a future real blockdevice write phase.

## In this phase

- read-only checks only
- harness proof binding is required
- snapshot/fingerprint is required
- result is only `READY` or `BLOCKED`

## Explicitly out of scope

- no write engine
- no dd/mkfs/parted/fdisk/sfdisk
- no mount/losetup
