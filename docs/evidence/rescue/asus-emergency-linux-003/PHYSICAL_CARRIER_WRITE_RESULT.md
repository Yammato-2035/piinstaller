# PHYSICAL_CARRIER_WRITE_RESULT — PI-RS-ASUS-CARRIER-BUILD-WRITE-004

## Status

**`physical_carrier_written_and_verified`**

## Write

| Feld | Wert |
|------|------|
| Start | 2026-08-06T21:08:48Z |
| Ende | 2026-08-06T21:10:26Z |
| Writer | `scripts/rescue-live/write-fat32-esp-rescue-usb.sh --execute-write` |
| Ziel | `/dev/sda` (Intenso Ultra Line, fp `ce2e34b7f5ea4e41`) |
| ISO-SHA256 | `ce3258f945ea2f973414ed6bdca29f884be9415f66e06a0e9110e6d6b0f87473` |
| Exit | **0** |
| Evidence | `docs/evidence/runtime-results/rescue/fat32_esp_write_20260806_210852/` |
| FAT UUID | `7EA0-B29E` |

## Readback

| Prüfung | Ergebnis |
|---------|----------|
| `verify-fat32-esp-rescue-usb.sh` | **OK** (vor und nach ASUS-GRUB-Patch) |
| Partitionen | `sda1` SETUPHELFER / SETUPHELFER_RESCUE (ESP), `sda2` SETUP_LOGS |
| VERSION | Projekt **1.10.2.0** auf ESP |
| SquashFS VERSION | **1.10.2.0** |
| ISO-SHA in evidence.json | match |
| Sentinels/Spooler/ASUS-Module im SquashFS | alle OK |
| ASUS-00…05 + RECOVERY in ESP `grub.cfg` | **OK** (nach Patch; Default = ASUS-00) |
| Fingerprint Gerät | unverändert `ce2e34b7f5ea4e41` |
| Intern NVMe angefasst | **nein** |

## Hinweis zum ASUS-Menü

Der erste FAT32-ESP-Write nutzte den bisherigen Menügenerator ohne ASUS-Profile.
Sofort danach: Generator erweitert, ESP-`grub.cfg` mit ASUS-00 als Default neu geschrieben,
Verify erneut grün. Payload/SquashFS unverändert aus dem Controlled ISO.
