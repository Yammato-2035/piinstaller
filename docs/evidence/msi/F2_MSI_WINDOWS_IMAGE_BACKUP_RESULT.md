# F.2 MSI Windows Image Backup — Execution Result

**Stand:** 2026-06-16  
**Ergebnis:** `blocked` (`blocked_insufficient_target_capacity`)  
**Workspace-Version:** 1.9.2.0  
**Runtime bei Preflight:** 1.9.1.0 (Gate grün)  
**Git HEAD vorher:** `0e6493e`

## Zusammenfassung

Kontrollierter F.2-Preflight mit Operator-Doppelbestätigung und Kapazitätsprüfung.  
**Kein Image-Backup gestartet** — externes USB-Ziel hat nicht genug freien Speicher für ein unkomprimiertes Raw-Image inkl. 5 % Reserve.

| Prüfung | Ergebnis |
|---------|----------|
| Phase 0 Runtime-Gate | grün |
| Phase 1 F.1 API-Smoke | grün (3 read-only MSI-Routen) |
| Phase 2 Backup-Ziel | `/dev/sda1` → `/media/gabriel/Backup` (ext4, extern) |
| Phase 3 Kapazität | **blockiert** |
| Phase 4 Operator-Bestätigungen | beide `true` |
| Phase 5 Image-Execution | **nicht ausgeführt** |

## Quelle / Ziel

| Rolle | Gerät | Größe |
|-------|-------|-------|
| Quelle (Windows) | `/dev/nvme0n1` | 2 000 398 934 016 B (~1,86 TiB) |
| Linux-System (blockiert) | `/dev/nvme1n1` | — |
| Backup-Ziel | `/dev/sda1` auf `/media/gabriel/Backup` | ~791 741 046 784 B frei |
| Rettungsstick (blockiert) | `/dev/sdb` | — |

**Benötigt (raw + 5 %):** 2 100 418 880 716 B  
**Verfügbar:** 791 741 046 784 B

## Geplante Pfade (nicht angelegt)

- Backup-Verzeichnis: `…/setuphelfer-msi-image-backups/20260616T210507Z/`
- Partial: `windows_nvme0n1_20260616T210507Z.img.partial` — **nicht erstellt**
- Final: `windows_nvme0n1_20260616T210507Z.img` — **nicht erstellt**
- SHA256 / Manifest / final.json — **nicht erstellt**

## Safety-Flags

| Flag | Wert |
|------|------|
| `no_restore` | true |
| `no_wipe` | true |
| `no_format` | true |
| `no_partition_write` | true |
| `ntfs_mounted` | false |
| `bitlocker_action_executed` | false |
| `restore_executed` | false |

## Explizit nicht ausgeführt

- Kein Restore, Wipe, Formatieren, Partitionieren
- Kein Schreiben auf `/dev/nvme0n1`, `/dev/nvme1n1`, `/dev/sdb`
- Kein direktes Schreiben auf `/dev/sda` als Blockdevice
- Kein NTFS-Mount, kein BitLocker-Bypass
- Kein `dd`, keine `.partial`-Datei

## Tests

- `test_msi_windows_image_backup_execution_v1.py` — 10 passed
- `test_windows_ntfs_detection_contract_v1.py` — passed
- `test_msi_windows_routes_readonly_v1.py` — passed

## Nächster Schritt

1. Externes Ziel mit **≥ ~2,1 TiB frei** für raw Image **oder** getestete Kompressionspipeline
2. F.2 erneut mit gleichem Gate
3. Danach **F.3** Image Verify / Restore-Preview Precheck (noch kein Restore)

## Evidence-Dateien

- `F2_MSI_WINDOWS_IMAGE_BACKUP_RESULT.json`
- `F2_MSI_WINDOWS_IMAGE_BACKUP_MANIFEST_REDACTED.json`
