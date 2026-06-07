# RESCUE MSI Boot & Telemetry ACK — Operator Result

**Prompt:** `RESCUE_MSI_BOOT_AND_TELEMETRY_ACK_INGEST_START_ASSISTANT_AUTOSTART_FIX`  
**Classified:** 2026-06-07T16:00:00+02:00  
**Workspace version:** 1.7.9.0

## Ergebnis

| Gate-Feld | Wert |
|-----------|------|
| `target_laptop_booted_from_stick` | **true** |
| `target_boot_stage` | `live_console` |
| `target_network_manual_connected` | **true** |
| `target_telemetry_health_reached` | **true** |
| `target_telemetry_ingest_ack` | **true** |
| `target_network_telemetry_validated` | **true** |
| `last_ack_id` | `rti-e5aa1b9979b346f8` |
| `last_ingest_at` | `2026-06-07T13:55:28Z` |
| `last_error_code` | null |
| `start_assistant_autostart_validated` | **false** |
| `windows_inspect_executable` | **false** |

## Bootloader / FAT32 / GRUB

**Nicht mehr Hauptblocker.** FAT32-ESP mit standalone `BOOTX64.EFI` (grub_mkstandalone), Label `SETUPHELFER`, GRUB-Menü sichtbar, MSI bootet bis Live-Konsole.

## Telemetrie

Manueller Push vom MSI erfolgreich. Backend-Health:

- `queue_depth`: 0
- `last_ingest_at`: 2026-06-07T13:55:28Z
- `last_ack_id`: rti-e5aa1b9979b346f8

## Aktiver Blocker

**`RESCUE_START_ASSISTANT_AUTOSTART_NOT_VALIDATED`**

GRUB-Einträge führen bis zur Konsole. Der Startassistent startet nicht automatisch auf tty1. WLAN und Telemetrie mussten manuell gestartet werden.

## Root Cause (Autostart)

1. `setuphelfer_start_assistant=1` wurde in systemd/Script nicht ausgewertet.
2. Race zwischen `getty@tty1` und Startassistent — kein getty-Drop-in.
3. `--boot-trigger` brach ab, wenn TTY noch nicht bereit (`setuphelfer_rescue_has_interactive_tty`).
4. `StandardOutput=journal` statt tty — whiptail nicht sichtbar auf tty1.

## Fix (Workspace 1.7.9.0)

- systemd-Unit mit `ConditionKernelCommandLine=setuphelfer_start_assistant=1`, tty1, `TERM=linux`, getty-Konflikt behoben.
- Startassistent schreibt `/run/setuphelfer-rescue/start-assistant-status.json`.
- Automatisierter Netzwerk-/Telemetrie-Flow im Assistenten.

## Nächster Operator-Schritt

`RESCUE_ISO_START_ASSISTANT_AUTOSTART_REBUILD_AND_USB_RECOPY_OPERATOR_RUN` — ISO rebuild, USB recopy, MSI-Boot mit Autostart-Validierung.
