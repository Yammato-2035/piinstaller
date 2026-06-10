# Storage Role Classification – Architektur

**Version:** `storage_role_classification_v1`  
**Modul:** `backend/core/storage_role_classification.py`

## Klassifikationsmodell

| Rolle | Bedeutung | write_allowed | Typisches Risiko |
|-------|-----------|---------------|------------------|
| `linux_system_disk` | Linux-System (live oder offline) | false | red |
| `windows_system_disk` | Windows-System (EFI+NTFS+Merkmale) | false | red |
| `mixed_system_disk` | EFI + Linux + NTFS gemischt | false | red |
| `rescue_stick` | Setuphelfer Rettungsstick | false | red |
| `backup_target` | Externes Ziel nach Prüfung | false (Phase 2) | yellow/green |
| `backup_source` | Bekannte Backup-Quelle | false | red |
| `external_data_disk` | Externer Datenträger | false | yellow |
| `internal_data_disk` | Interner Datenträger | false | yellow |
| `unknown_disk` | Unzureichende Merkmale | false | yellow |

**Confidence:** `high` | `medium` | `low` — niedrige Confidence → `review_required`, nie grün ohne belastbare Merkmale.

## API (read-only)

- `GET /api/partitions/scan` — je Disk `storage_role` + Top-Level `storage_roles`
- `GET /api/partitions/storage-roles` — nur Klassifikationsliste
- `GET /api/partitions/hardstop-preview` — auto-Klassifikation aus Scan

## Wiederverwendung Partitionshelfer

Frontend nutzt `disk.storage_role` mit Vorrang; Fallback nur mit Kennzeichnung.

Komponenten: `PartitionOverviewCards`, `PartitionSafetyStatusPanel`, `PartitionHardstopPanel`.

## Wiederverwendung Rettungsstick

- Gleiche Engine über `classify_disk_storage_role()` / `classify_scan_disks()`
- Rescue Discovery (`storage_facade.py`) kann Snapshot mit Rollen anreichern
- Hardstop-Codes: `target_is_rescue_stick`, `target_is_windows_system_disk`, …

## Windows-Erkennung

Kriterien (ohne Gerätenamen):

1. EFI-Partition (`parttypename`, vfat, Größe)
2. NTFS-Partition
3. Mindestens eines: Microsoft Basic Data, Recovery, großes NTFS, BitLocker-Hinweis

## Linux-Erkennung

- Live-Root (`mountpoint=/`)
- Oder EFI + Linux-FS + GPT-Typ / Boot-Merkmale

## Backup-Ziel

- Extern/USB + Mount unter `/media/` — **medium** confidence
- Grün nur bei `high` confidence (z. B. Setuphelfer-Backup-Struktur — Erweiterung Phase 3)

## Grenzen

- Kein Zugriff auf ungemountete `EFI/Microsoft/Boot` ohne Mount
- Offline-Windows: Partitionstabelle-Heuristik (kein Registry/BCD)
- Hardware-Tests auf echter Windows-NVMe ausstehend

## Hardstop-Logik

`partition_hardstop.evaluate_partition_hardstops` wertet `storage_role` und `evidence` aus.

Neue Codes: `target_is_windows_system_disk`, `target_is_linux_system_disk`, `target_is_rescue_stick`, `target_role_uncertain`, `target_contains_boot_partitions`, `target_contains_os_partitions`.
