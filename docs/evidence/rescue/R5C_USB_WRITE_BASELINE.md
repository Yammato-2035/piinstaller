# R.5C — USB Write Baseline

**Datum:** 2026-06-13  
**Quelle:** `fat32_esp_write_20260613_171403` (redacted, keine Seriennummern)

## Write-Ergebnis

| Feld | Wert |
|------|------|
| **write_executed** | **true** |
| **write_status** | `success` |
| **verify_status** | `success` |
| **ISO SHA256** | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` |
| **FAT UUID** | `FE8C-7F79` (Volume-Label-Gate in grub.cfg) |

## Stick-Layout (Verify OK)

| Komponente | Status |
|------------|--------|
| LABEL | `SETUPHELFER` |
| GPT_NAME | `SETUPHELFER_RESCUE` |
| EFI/BOOT/BOOTX64.EFI | **OK** (standalone grub_mkstandalone) |
| boot/grub/grub.cfg | **OK** (inkl. `set theme=`) |
| live/vmlinuz | **OK** |
| live/initrd.img | **OK** |
| live/filesystem.squashfs | **OK** (~1,22 GB) |
| setuphelfer/rescue/boot-branding.txt | **OK** |
| standalone BOOTX64.EFI | **OK** (differs from ISO — erwartet) |

## RS-001 (vor MSI-Boot)

| Feld | Wert |
|------|------|
| **rs001_status** | **red** |
| **rs001_reason** | USB written and verified; **Hardware-Boot noch nicht bewiesen** |

## Write-Time Evidence auf Stick (pre-boot)

| Pfad | Rolle |
|------|-------|
| `setuphelfer/rescue/evidence.json` | Writer-Staging-Metadaten (ISO-SHA, Payload-Hashes) |
| `setuphelfer/rescue/version.json` | Projektversion `1.7.17.0` |

**Kein** Runtime-Baum `/setuphelfer-evidence/` zum Zeitpunkt des Baseline-Snapshots (vor/nach MSI — siehe R5C_STICK_EVIDENCE_INVENTORY).

## Redaction

Seriennummern, `/dev/sd*` Pfade und Host-Pfade in committed Evidence **nicht** wiedergeben.
