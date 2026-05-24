# Rettungsstick – Partitions-Handoff (Architektur)

## Daten vom Partitionshelfer (read-only)

| Feld / API | Nutzung auf Rettungsstick |
|------------|---------------------------|
| `storage_safety` | Zielklassifikation, Hardstops, write_guard |
| `manifest_layout_preview.layout` | Erwartete Filesysteme, Mountpoints, Boot/EFI |
| `restore_handoff_preview.handoff_sources` | Verknüpfung Hardstop + Manifest + Verify |
| `required_next_gates` | VERIFY, BACKUP_BEFORE_OVERWRITE, PARTITION_HARDSTOP |
| `evidence_refs` | Pfade zu MANIFEST.json / Evidence |

## Read-only auf Rettungsstick-Vorbereitung

- Manifest lesen (Allowlist)
- Inspect/write_guard erneut ausführen (kein Cache-Vertrauen allein)
- Handoff anzeigen – **kein** Restore-Start aus Partitions-UI

## Gates vor echtem Write/Restore

1. Runtime Phase 0 (Version, Drift, Dienst aktiv)
2. Partition Hardstop nicht `blocked`
3. Verify (mind. shallow; deep nach Policy)
4. Backup-before-overwrite satisfied
5. Rettungsstick Live-OS bootfähig (noch **offen**)
6. Restore Execution explizit freigegeben (eigener Flow)

## Handoff-Struktur (Ziel)

```json
{
  "target_device": "/dev/sdX",
  "storage_safety": {},
  "manifest_layout": {},
  "verify_evidence": {},
  "restore_execution_allowed": false
}
```

## Noch fehlend (blocked)

- Live-OS / ISO-Build / `lb build`
- debootstrap / chroot / apt auf Stick
- Boot-Test, Hardware-Test, EFI-Recovery
- Restore Execution auf Zielplatte
- Debian/Ubuntu/Mint Provisioning

## Referenz

`docs/evidence/rescue/RESCUE_STICK_PARTITION_HANDOFF_READONLY.md`
