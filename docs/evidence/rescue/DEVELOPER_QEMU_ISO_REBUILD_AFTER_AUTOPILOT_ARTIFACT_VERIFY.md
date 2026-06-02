# Developer QEMU ISO Rebuild After Autopilot Fix — Artifact Verify

**Datum:** 2026-06-03

## Aktuelles ISO (noch Pre-Fix-Squashfs)

| Feld | Wert |
|------|------|
| ISO vorhanden | **yes** (stale) |
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 511705088 |
| SHA256 | `3ee02b364bf5a35106591b67fb975f0864390cb413088c0d000e54e770dd48c1` |
| file | ISO 9660 bootable SETUPHELFER_RESCUE |
| SHA neu vs. vorherigem Developer-QEMU-ISO | **no** (identisch) |

## Bewertung

Post-Fix-Rebuild **nicht** durchgeführt → **blocked_same_iso** / kein neues Artefakt.

Nach Operator-Rebuild: SHA **muss** von `3ee02b36…` abweichen und Squashfs-Validator Exit 0 liefern.

## Status

**blocked_same_iso**
