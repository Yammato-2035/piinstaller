# R.8B — Stick R.6 Static Check

**Datum:** 2026-06-13  
**Methode:** read-only mount `/dev/sdb1` (ro)

## Stick-Inhalt (aktuell = pre-R.8 Write)

| Check | Ergebnis |
|-------|----------|
| `live/filesystem.squashfs` SHA | `983492b08f7459d7a7276710760c8c1b7c40e6750673fa39f3046c9f5c540856` |
| R.8 ISO Squashfs SHA | `18d613e5…` (im Squashfs-Inhalt — **nicht** auf Stick) |
| `boot-evidence-init` im Stick-Squashfs | **MISSING** |
| MANIFEST `source_head=d62b4a1` auf Stick | **nein** (alter Build) |

## Bewertung

Stick enthält **noch nicht** die R.8-ISO. Erwartbar — Write nicht erfolgreich.

Nach erfolgreichem Write + Verify muss Squashfs-Inspection erneut:

- `setuphelfer-rescue-boot-evidence-init` **FOUND**
- `RESCUE_PERSISTENCE_VERSION = 4`
- `initialize_boot_evidence_marker`

## Referenz (R.8 ISO Post-Build)

Diese Komponenten sind in der **neuen ISO** nachgewiesen (`R8_SQUASHFS_R6_HOOK_CHECK.md`).
