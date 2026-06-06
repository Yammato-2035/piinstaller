# RESCUE_USB_MSI_UEFI_BOOT_OPERATOR_RESULT

**Datum:** 2026-06-06  
**Prompt:** `RESCUE_USB_MSI_UEFI_BOOT_OPERATOR_RUN` → Triage → Rebuild-Vorbereitung `RESCUE_ISO_MSI_FIRMWARE_SERIAL_MARKER_REBUILD_OPERATOR_RUN`  
**Stick:** `/dev/sdb` Ultra Line · ISO SHA256 `09b9482a…` (vor Firmware-Rebuild)

## Ergebnis (Kurz)

**UEFI-Boot vom Setuphelfer-Rescue-USB auf MSI-Laptop erfolgreich gestartet — Live-System nur teilweise funktionsfähig.**

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Stick im UEFI-Menü sichtbar | **ja** (Operator) |
| GRUB / Rescue-Live startet | **ja** |
| Grafik (GeForce) | Boot sichtbar — Detail-Modus offen |
| Intel WLAN Firmware | **fehlt im Image** (`iwlwifi-9000-…ucode`) |
| Intel BT Firmware | **fehlt im Image** (`intel/ibt-17-16-1.sfi`) |
| Netzwerk/Telemetrie zum Developer-Laptop | **nicht bestätigt** |
| `setuphelfer-serial-boot-markers.service` | **FAILED** (QEMU-Lab-Unit auf Hardware) |
| Windows-Inspect | **nicht ausgeführt** (korrekt blockiert) |

## Boot-Meldungen (Operator)

```text
iwlwifi 0000:00:14.3: firmware: failed to load iwlwifi-9000-pu-b0-jf-b0-37.ucode (-2)
bluetooth hci0: firmware: failed to load intel/ibt-17-16-1.sfi (-2)
[FAILED] Failed to start setuphelfer-serial-boot-markers.service - Setuphelfer serial boot markers (QEMU lab).
```

## partprobe / Stick

Unverändert gegenüber Write-Ingest: `usb_partition_probe_warning` = `recursive_partition_warning_after_isohybrid_write` — kein Write-Failure.

## Klassifikation (Pflicht)

| Feld | Wert |
|------|------|
| `msi_uefi_boot_status` | **partial_success** |
| `target_laptop_booted_from_stick` | **true** |
| `windows_inspect_executable` | **false** |

## Blocker (aktiv)

- `RESCUE_ISO_INTEL_WIFI_BT_FIRMWARE_MISSING` — ISO-Rebuild mit Paketliste ausstehend (Workspace-Fix vorbereitet)
- `RESCUE_SERIAL_BOOT_MARKERS_HARDWARE_INCOMPATIBLE` — Fix `ConditionVirtualization=qemu` im Workspace; wirksam nach ISO-Rebuild
- `RESCUE_TARGET_NETWORK_TELEMETRY_NOT_VALIDATED`
- `WINDOWS_INSPECT_BLOCKED_UNTIL_LIVE_NETWORK_VALIDATED`

## Resolved

- `RESCUE_USB_BOOT_NOT_VALIDATED_ON_TARGET`

## Secrets

Keine Secrets in dieser Datei.
