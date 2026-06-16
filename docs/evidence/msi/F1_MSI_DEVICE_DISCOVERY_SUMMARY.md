# F.1 MSI Device Discovery Summary

**Run:** F1-MSI-WINDOWS-READONLY-PRECHECK  
**Zeitpunkt:** 2026-06-16T20:32:01Z  
**Modus:** read-only (kein Mount, kein Write)

## Host

| Feld | Wert |
|------|------|
| DMI Vendor | ASUSTeK COMPUTER INC. |
| DMI Product | ROG Strix G713PI_G713PI |
| BootCurrent (efibootmgr) | Ubuntu (`nvme1n1` EFI) |
| Windows Boot Manager | vorhanden → `nvme0n1` EFI-Partition |

Hinweis: Teststrang „MSI“ bezeichnet den **Windows-Quell-Datenträger** im Dual-Boot-Setup, nicht zwingend MSI-DMI-Branding.

## Gerätetabelle

| Gerät | Größe | Modell | Transport | FSTYPE/Partitionen | Windows | NTFS | EFI | BitLocker | Rolle | Risiko |
|-------|------:|--------|-----------|-------------------|---------|------|-----|-----------|-------|--------|
| nvme0n1 | 1,8T | Samsung SSD 980 PRO | nvme | ntfs×4, vfat EFI, 16M MSR | **ja** | **ja** | **ja** | nicht_detektiert | msi_windows_source_candidate | gelb |
| nvme1n1 | 1,8T | Samsung SSD 980 PRO | nvme | ext4 `/`, vfat `/boot/efi` | nein | nein | ja (Linux) | — | linux_system_disk | rot (nicht überschreiben) |
| sda | 931G | HGST (USB) | usb | ext4 Label Backup | nein | nein | nein | — | backup_target_candidate | grün |
| sdb | 59G | Intenso Ultra Line | usb | vfat SETUPHELFER/LOGS | nein | nein | nein | — | rescue_stick | grün |

Seriennummern: nur **redacted** in committed Evidence (`sha256:…`).

## Entscheidung

| Kriterium | Ergebnis |
|-----------|----------|
| Windows-Quelle eindeutig | **ja** → `/dev/nvme0n1` |
| EFI | ja (`nvme0n1p2` vfat, Windows Boot Manager) |
| NTFS | ja (p1, p4, p5, p6) |
| BitLocker (blkid) | `not_detected` (kein TYPE=BitLocker; keine Entschlüsselungsbehauptung) |
| Backup-Ziel extern | **ja** → `/dev/sda` ext4 „Backup“ |
| image_backup_plan | **erlaubt** (F.2) |
| image_backup_execute | **nein** (F.1) |

## Blockiert

- Schreiben auf `nvme0n1` / `nvme1n1`
- Restore/Wipe/Linux-Install in F.1

Rohdaten (redacted): `F1_MSI_DEVICE_DISCOVERY_RAW_REDACTED.txt`
