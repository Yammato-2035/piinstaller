# RESCUE ISO Network Onboarding — Post-Build Validation

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_ISO_NETWORK_ONBOARDING_POST_BUILD_VALIDATION_AND_USB_REWRITE_HANDOFF`  
**Workspace:** `1.7.5.0` · **HEAD:** `5668fa8`  
**Build:** `LB_EXIT=0` · **UEFI post-patch:** `validate_exit=0`

## Ergebnis

**Post-Build-Validierung grün für ISO-Artefakt und SquashFS-Inhalt.**  
USB-Rewrite-Handoff freigegeben — **kein dd durch Agent**, Readback und MSI-Retest bleiben Operator-Pflicht.

| Prüfung | Ergebnis |
|---------|----------|
| ISO vorhanden | ja |
| ISO SHA256 | `86cba7eb550bcdb0562a414f79d78db58c908d5d743d474365eda0bcb638e5fc` |
| ISO Größe | 683671552 bytes (~652 MiB) |
| UEFI-Validator | **Exit 0** |
| SquashFS-Validator | **Exit 0** |
| Network-Onboarding-Scripts im SquashFS | **ja** (alle 4 + common) |
| nmcli / NetworkManager / rfkill / iw / ping | **ja** |
| systemd-Units (onboarding, media, telemetry, task-pull) | **ja**, wants aktiv |
| iwlwifi-9000 + ibt-17-16-1 Firmware | **ja** |
| serial-boot-markers QEMU-only | **ja** (`ConditionVirtualization=qemu`) |
| Custom ISOLINUX-Menüeinträge | **fehlen** (Warnung, kein Blocker) |
| Bundle `project_version` im SquashFS | `1.7.3.0` (Runtime-Bundle-Drift, Warnung) |

## Vorherige ISO (Stick noch alt)

| Feld | Alt (Stick) | Neu (Build) |
|------|-------------|-------------|
| SHA256 | `9ef1b330…` | `86cba7eb…` |
| Größe | 620756992 | 683671552 |

**Stick `/dev/sdb` enthält noch die alte ISO** — `usb_write_sha256_verified` gilt erst nach Rewrite + Readback gegen `86cba7eb…`.

## Validator-Ausgabe

```text
validate-rescue-iso-uefi-boot.sh     → Exit 0
validate-rescue-iso-squashfs.sh      → Exit 0
```

## SquashFS — Network-Onboarding (manuell verifiziert)

```text
OK usr/local/sbin/setuphelfer-rescue-network-onboarding
OK usr/local/sbin/setuphelfer-rescue-media-check
OK usr/local/sbin/setuphelfer-rescue-telemetry-push
OK usr/local/sbin/setuphelfer-rescue-task-pull
OK usr/local/sbin/setuphelfer-rescue-common.sh
OK usr/bin/nmcli
OK usr/sbin/NetworkManager
OK usr/sbin/rfkill
OK usr/sbin/iw
OK usr/bin/ping
```

Chroot-Pakete u.a.: `network-manager`, `rfkill`, `iw`, `whiptail`, `firmware-iwlwifi`.

## Warnungen (kein Fake-Green, kein USB-Blocker)

1. **`RESCUE_ISO_BOOT_MENU_CUSTOM_ENTRIES_MISSING`** — Hook `020-setuphelfer-rescue-boot-menu.hook.binary` hat keine Extra-Labels in `isolinux/live.cfg` hinterlassen. Default-Boot + manuell `setuphelfer-network` / Services bleiben nutzbar.
2. **`RUNTIME_BUNDLE_VERSION_DRIFT_IN_SQUASHFS`** — `/opt/setuphelfer-rescue` meldet `1.7.3.0`; Overlay-Scripts/Units sind aus Build-Tree HEAD `5668fa8`. Separates Bundle-Refresh empfohlen, blockiert USB-Rewrite nicht.
3. **`RUNTIME_DEPLOY_DRIFT_1_7_5_0_PENDING`** — Backend API `1.7.4.1` vs Workspace `1.7.5.0`; Telemetrie-Proxy unabhängig.

## Noch nicht grün (ehrlich)

- `usb_write_sha256_verified` — ausstehend (neue ISO)
- `target_network_link_established` / Telemetrie-ACK — MSI-Retest nach Stick-Rewrite
- `windows_inspect_executable` — **false**

## Nächster Schritt

`RESCUE_USB_REWRITE_OPERATOR_RUN` — siehe `RESCUE_USB_REWRITE_OPERATOR_HANDOFF.md`

## Nicht ausgeführt

dd, USB-Schreiben, Windows-Inspect, Backup, Restore, Push.
