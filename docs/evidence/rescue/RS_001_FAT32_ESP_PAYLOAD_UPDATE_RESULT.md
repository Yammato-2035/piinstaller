# RS-001 FAT32 ESP Payload Update — React Launcher Fix 1.7.10.1

**Datum:** 2026-06-09  
**HEAD:** `dad1db5`  
**Status:** **blocked_operator_sudo_required**

## SquashFS (bereit)

| Feld | Wert |
|------|------|
| Version | `1.7.10.1` |
| Pfad | `build/rescue/filesystem.squashfs.repacked-1.7.10.1` |
| `new_squashfs_sha256` | `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc` |
| `old_stick_sha256` | `a54aae1d902523cf08b37105b1f6001e048d610b57210520ea2e1a649b3fe820` |
| Content check | **success** (`RS_001_REACT_SHELL_LAUNCHER_SQUASHFS_CONTENT_CHECK.md`) |

## Payload-Update (Agent-Lauf)

| Feld | Wert |
|------|------|
| `payload_update_status` | **blocked** |
| `verify_status` | **not_run** |
| `stick_squashfs_hash_ok` | **false** (Stick noch alt) |
| Grund | `sudo` Passwort erforderlich — kein interaktives Terminal |
| Safety gate (lsblk) | **passed** (`/dev/sdb`, Ultra Line, SETUPHELFER vfat) |
| Plan generiert | **yes** (`payload_update_executed=false`) |

## Operator-Befehle (nächster Schritt)

```bash
cd /home/volker/piinstaller

./scripts/rescue-live/update-fat32-esp-live-payload.sh \
  --target /dev/sdb \
  --new-squashfs build/rescue/filesystem.squashfs.repacked-1.7.10.1 \
  --operator-confirm-update \
  --confirm-phrase "UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD" \
  --execute-update

./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh \
  --target /dev/sdb \
  --expected-squashfs-sha256 0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc
```

## RS-001

```text
RS-001: yellow
Reason: launcher fix squashfs ready; stick payload update pending operator sudo
Ready for operator hardware retest: false (until payload update + verify)
```
