# CONTROLLED_ISO_BUILD_RESULT — PI-RS-ASUS-CARRIER-BUILD-WRITE-004

Stand: 2026-08-06T20:23Z  
Workspace: `/home/volker/piinstaller-asus-emergency-linux-telemetry-003`  
Branch: `pi-rs-asus-emergency-linux-telemetry-003`

## Ergebnis

**Status: `passed`**

## Identitäten

| Feld | Wert |
|------|------|
| Run-ID | `asus-carrier-004-20260806T195318Z` |
| ISO-Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| ISO-SHA256 | `ce3258f945ea2f973414ed6bdca29f884be9415f66e06a0e9110e6d6b0f87473` |
| ISO-Größe | 1443889152 bytes (~1,34 GiB) |
| Ownership | `root:root` (Build/Patch unter sudo; erwartet) |
| Projektversion | **1.10.2.0** |
| Payload-SoT | **1.10.0.17** |
| Bundle `source_head` | `2deb694b` (Commit zum Bundle-Zeitpunkt; Build-Wiring danach im Worktree nachgezogen) |
| Profil | `standard` |

## Build-Schritte

1. Runtime-Bundle + Rescue-UI + `prepare-controlled-live-build-tree.sh` (standard)
2. `run-controlled-iso-build-with-logging.sh --operator-confirm-build` → `LB_EXIT=0`
3. UEFI-Post-Patch (offiziell) → Validate exit 0
4. **Nachprüfung:** finales `grub.cfg` enthielt zunächst nur Default-Eintrag (UEFI-Remaster)
5. Fix: `patch-rescue-iso-uefi-x64.sh` bindet GRUB-Snippet inkl. ASUS-00…05/RECOVERY; Isolinux-ASUS-Labels
6. In-Place-Repatch → SHA256 `ce3258f9…`; UEFI-Validate erneut **0**

## Verifikation

| Prüfung | Ergebnis |
|---------|----------|
| `validate-rescue-iso-uefi-boot.sh` | OK (BIOS+EFI+BOOTX64+Hybrid) |
| `validate-rescue-iso-squashfs.sh` | OK |
| SquashFS VERSION | `1.10.2.0` |
| SquashFS `version.json` | `1.10.2.0` / Track `pi_rs_asus_emergency_linux_telemetry_003` |
| ASUS-Module im SquashFS | alle 10 OK |
| systemd-Units (Sentinel/Spooler/Autocapture) | alle 5 OK |
| GRUB ASUS-00…05 + RECOVERY | vorhanden (13 menuentries) |
| Isolinux ASUS-Labels | vorhanden |
| Fremd-ISO aus anderem Worktree wiederverwendet | **nein** |

## Abgleich Workspace ↔ Payload ↔ Carrier-Metadaten

| Quelle | Version / Commit |
|--------|------------------|
| Workspace `config/version.json` | 1.10.2.0 |
| Workspace `rescue_payload_version` | 1.10.0.17 |
| ISO SquashFS VERSION | 1.10.2.0 |
| ISO SquashFS version.json | 1.10.2.0 |
| Bundle MANIFEST source_head | 2deb694b |

Hinweis: Payload-Datei `rescue_payload_version.json` liegt im Bundle unter dem Workspace-`config/`-Pfad der Runtime; Carrier-Write nutzt dieses ISO nach ASUS-Menü-Repatch.

## USB-Write

Noch **nicht** freigegeben (`usb_write_allowed=false` bis doppelte Operatorbestätigung).
