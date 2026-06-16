# R.8 — Ready for USB Write Decision

**Datum:** 2026-06-13

## Kriterien

| Kriterium | Erfüllt |
|-----------|---------|
| LB_EXIT=0 | **ja** |
| ISO neu (SHA256 ≠ pre-R.6) | **ja** (`18d613e5…` ≠ `f94a1c39…`) |
| SHA256 dokumentiert | **ja** |
| R.6 Hook im Squashfs | **ja** (`boot-evidence-init`) |
| R.6 persistence v4 | **ja** |
| boot_marker support | **ja** (`initialize_boot_evidence_marker`) |
| MANIFEST `source_head=d62b4a1` | **ja** |
| R.4 Browser/Kiosk Stack | **ja** |
| UEFI `BOOTX64.EFI` | **ja** |
| `filesystem.squashfs` | **ja** |
| `x-www-browser` absent | **ja** |

## Sub-Checks

| Phase | Ergebnis |
|-------|----------|
| Post-Build Summary | PASS |
| SquashFS R6 Hook | PASS |
| SquashFS R4 Regression | PASS |
| Boot Path Static | PASS (ISO-GRUB minimal = yellow, kein Blocker) |

## Status

# **ready_for_r8_usb_write**

## Voraussetzung USB-Write (Operator)

```bash
export OPERATOR_USB_WRITE_FREIGABE=1
# USB_TARGET + Gates setzen
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh --execute-write ...
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh
```

Erwartete ISO-SHA256 beim Write: `18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390`

## Nächster Schritt

**R.8 USB WRITE + VERIFY** → danach **MSI-Boot** → `setuphelfer-evidence/boot/boot_marker.md` prüfen.

## Verbotene Aktionen (eingehalten)

Kein USB-Write, MSI-Boot, Deploy in dieser Validierung.
