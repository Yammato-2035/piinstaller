# Deploy Real Write Guard (DE)

## Ziel

Sicherheits-, Session- und Snapshot-Guard fuer spaeteren Real-Write auf Blockdevices.

## In dieser Phase

- nur read-only Pruefungen
- Harness-Proof-Bindung verpflichtend
- Snapshot/Fingerprint verpflichtend
- Ergebnis nur `READY` oder `BLOCKED`

## Ausdruecklich nicht enthalten

- keine Write-Engine
- kein dd/mkfs/parted/fdisk/sfdisk
- kein mount/losetup
