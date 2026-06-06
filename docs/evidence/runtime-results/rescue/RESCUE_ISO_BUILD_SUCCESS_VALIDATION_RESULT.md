# RESCUE_ISO_BUILD_SUCCESS_VALIDATION_RESULT

**Datum:** 2026-06-06  
**Prompt:** `RESCUE_ISO_BUILD_SUCCESS_VALIDATION_AND_USB_REWRITE_PREP`  
**HEAD:** `8fe31d9` · **Version:** `1.7.4.4`

## Ergebnis

**Teilweise grün — kein Fake-Green, kein USB-Rewrite-Handoff.** Build `LB_EXIT=0`, Firmware im SquashFS nachgewiesen. UEFI-Validator **Exit 34** und **NetworkManager/nmcli fehlen** im SquashFS → USB-Schritt blockiert.

## Build

| Feld | Wert |
|------|------|
| LB_EXIT | **0** |
| ISO | `binary.hybrid.iso` (551 MiB) |
| SHA256 | `dc35138768ee659273ac0949a26b468d911a9dac3ca2e0c854b01481609041f8` |
| SquashFS | vorhanden (468 MiB) |
| Vorherige Stick-SHA256 | `09b9482a…` |

## UEFI-Validator

| Prüfung | Ergebnis |
|---------|----------|
| Exit | **34** (`RESCUE-UEFI-003 isolinux_only_iso`) |
| BOOTX64.EFI | **nein** |
| boot/grub/efi.img | **nein** |
| isolinux.bin | **ja** |

→ **`RESCUE_ISO_UEFI_VALIDATOR_FAILURE_TRIAGE`**

## SquashFS-Firmware

| Prüfung | Ergebnis |
|---------|----------|
| `iwlwifi-9000*.ucode` | **ja** (34, 38, 46; **-37 fehlt**) |
| `intel/ibt-17-16-1.sfi` | **ja** |
| `regulatory.db` / wireless-regdb | **ja** |
| NetworkManager Unit | **nein** (Symlink ohne `/lib/systemd/system/NetworkManager.service`) |
| nmcli | **nein** |

Build-Log: `bookworm/non-free-firmware` ✓ · Pakete `firmware-iwlwifi`, `firmware-intel-sound`, `network-manager` installiert — NM später aus SquashFS-Inhalt nicht funktional.

## Serial-Marker

SquashFS enthält **alte** Unit mit `TTYPath=/dev/ttyS0` (ohne `ConditionVirtualization=qemu`) — **nicht resolved**.

## Blocker

**Resolved:** `RESCUE_ISO_INTEL_WIFI_BT_FIRMWARE_MISSING`, Parent-Archive-Areas, APT-Component-Fehler

**Aktiv:** UEFI-Validator, NetworkManager/nmcli, Serial-Marker, USB-Rewrite, MSI-Boot, Telemetrie, Windows-Inspect

## Next Prompt

**`RESCUE_ISO_UEFI_VALIDATOR_FAILURE_TRIAGE`**

Parallel bei NM: **`RESCUE_ISO_NETWORKMANAGER_MISSING_AFTER_REBUILD`**

Erst nach UEFI+NM grün: **`RESCUE_USB_REWRITE_OPERATOR_AFTER_MSI_FIRMWARE_REBUILD`**

## Operator-Handoff (noch nicht freigegeben)

```bash
# Erst nach UEFI-Patch + NM-Fix + erneuter Validierung:
ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
TARGET=/dev/sdb
sha256sum "$ISO"
lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN,FSTYPE,LABEL,MOUNTPOINTS /dev/sda /dev/sdb
```

## Nicht ausgeführt

USB-dd · MSI-Retest · Windows-Inspect · Deploy · Push · Commit (Code)

## Commit / Push

Evidence-Commit in Phase 9 — Push **nein**
