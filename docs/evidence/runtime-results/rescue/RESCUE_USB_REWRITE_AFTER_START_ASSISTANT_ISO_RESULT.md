# RESCUE USB Rewrite — nach Start Assistant ISO (1.7.7.0)

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_USB_REWRITE_AFTER_START_ASSISTANT_ISO_OPERATOR_RUN`  
**HEAD:** `0ca7f65` (vor Evidence-Commit) · **Version:** `1.7.7.0`

## Ergebnis

**USB-Write vollständig verifiziert** — Operator-Block-Readback SHA256 stimmt exakt mit ISO überein. Bootartefakte und Branding auf dem Stick nachgewiesen.

**MSI-Boot-Test freigegeben.**

| Prüfung | Ergebnis |
|---------|----------|
| ISO SHA256 | `3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7` ✓ |
| ISO Größe | 683671552 bytes ✓ |
| Zielgerät `/dev/sdb` | Ultra Line, 59G, Serial `24111412110212` ✓ |
| FSTYPE / Label | iso9660 `SETUPHELFER_RESCUE` ✓ |
| Operator-`dd` | 683671552 Bytes kopiert ✓ |
| **Block-Readback SHA256** | **`3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7`** ✓ |
| Readback = ISO SHA | **Match** ✓ |
| Boot-Artefakte ro-Mount | **OK** |
| Boot-Menü/Branding auf Stick | **OK** |

## ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 683671552 bytes (~652 MiB) |
| SHA256 | `3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7` |

## Zielgerät

| Feld | Wert |
|------|------|
| Device | `/dev/sdb` |
| Modell | Ultra Line |
| Serial | `24111412110212` |
| Transport | usb |
| Partition | `/dev/sdb1` 652M iso9660 `SETUPHELFER_RESCUE` |
| Nicht verwendet | `/dev/sda` (HGST Backup), `/dev/nvme*` |

## Readback SHA256 (Operator-Ingest)

Quelle: Terminal-Session Operator (sudo python3 Block-Read von `/dev/sdb`, erste ISO_SIZE Bytes).

```text
ISO_SHA256:                3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7
USB_BLOCK_READBACK_SHA256: 3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7
Match: yes
Methode: sudo dd + sudo python3 block-read, 683671552 Bytes
```

Agent unabhängig bestätigt: ISO `sha256sum` identisch.

## Bootartefakte (ro-Mount `/dev/sdb1`)

```text
EFI/BOOT/BOOTX64.EFI     present (3,1M)
boot/grub/efi.img        present (16M)
isolinux/isolinux.bin    present (38K)
isolinux/isolinux.cfg    present — MENU TITLE Setuphelfer Rettungsstick
isolinux/live.cfg        present — alle Custom-Labels
```

**Boot-Menü-Einträge auf Stick:**

- Setuphelfer Rettung starten (`setuphelfer-rescue-default`)
- Netzwerk-Assistent (`setuphelfer-rescue-network`)
- MSI/NVIDIA-Kompatibilitätsmodus (`setuphelfer-rescue-msi-compat`)
- Diagnosemodus (`setuphelfer-rescue-diagnose`)
- Start in RAM / Media-Check (`setuphelfer-rescue-toram`)
- Neustart / Herunterfahren (`reboot.c32` / `poweroff.c32`)

Mount: `udisksctl mount -b /dev/sdb1 --options ro` — danach unmount + sync.

## Gate-Status

| Feld | Wert |
|------|------|
| iso_post_build_validated | true |
| iso_uefi_validated | true |
| boot_menu_branding_validated | true |
| start_assistant_present_in_iso | true |
| network_onboarding_present_in_iso | true |
| telemetry_push_present_in_iso | true |
| usb_stick_written | yes |
| usb_write_sha256_verified | true |
| usb_mount_boot_artifacts_verified | true |
| usb_stick_matches_current_iso | true |
| target_laptop_booted_from_stick | false |
| target_network_telemetry_validated | false |
| target_telemetry_ingest_ack | false |
| windows_inspect_executable | false |

## Resolved Blocker

- `RESCUE_USB_REWRITE_PENDING_OPERATOR`

## Aktive Blocker

- `RESCUE_MSI_BOOT_AUTOMATED_TELEMETRY_ACK_PENDING`
- `WINDOWS_INSPECT_BLOCKED_UNTIL_LIVE_NETWORK_VALIDATED` (RESCUE-UEFI-005)

## Nächster Schritt

`RESCUE_MSI_BOOT_START_ASSISTANT_NETWORK_TELEMETRY_OPERATOR_RUN`

## Nicht ausgeführt

dd (Agent), erneutes Schreiben, Partitionieren, Backup, Restore, Windows-Inspect, Push, Secrets geloggt.
