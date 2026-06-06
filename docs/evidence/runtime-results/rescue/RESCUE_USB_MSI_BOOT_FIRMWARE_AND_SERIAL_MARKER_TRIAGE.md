# RESCUE_USB_MSI_BOOT_FIRMWARE_AND_SERIAL_MARKER_TRIAGE

**Datum:** 2026-06-06  
**Prompt:** `RESCUE_USB_MSI_BOOT_FIRMWARE_AND_SERIAL_MARKER_TRIAGE` → Workspace-Fix `RESCUE_ISO_MSI_FIRMWARE_SERIAL_MARKER_REBUILD_OPERATOR_RUN`  
**HEAD (Workspace):** `345187b` → Version **1.7.4.2** (Rebuild-Commit) · **Runtime:** `1.7.4.1` (Deploy nach Commit ausstehend)

## Operator-Beobachtung (MSI UEFI-Boot)

| Feld | Wert |
|------|------|
| Ziel | MSI-Laptop, Intel Core i7, GeForce, Windows vorhanden |
| UEFI-Boot vom Stick | **gestartet** (Rescue-Live kam hoch) |
| Grafik | Boot sichtbar (Details vom Operator noch zu dokumentieren) |
| Intel WiFi | **firmware load failed** |
| Intel Bluetooth | **firmware load failed** |
| `setuphelfer-serial-boot-markers.service` | **FAILED** (QEMU-Lab-Unit auf echter Hardware) |

### Kernel-Meldungen (Auszug)

```text
iwlwifi 0000:00:14.3: firmware: failed to load iwlwifi-9000-pu-b0-jf-b0-37.ucode (-2)
bluetooth hci0: firmware: failed to load intel/ibt-17-16-1.sfi (-2)
[FAILED] Failed to start setuphelfer-serial-boot-markers.service - Setuphelfer serial boot markers (QEMU lab).
```

## Root Cause

### 1. Fehlende Firmware im Rescue-ISO

- `prepare-controlled-live-build-tree.sh` setzt `--firmware-chroot false` (bewusst, lb-fetch war broken).
- Paketliste enthielt **keine** `firmware-iwlwifi` / `firmware-intel-sound`.
- Rescue-Netzwerkmenü (`setuphelfer-rescue-network-menu.sh`) nutzt **WLAN über nmcli** — `network-manager` fehlte ebenfalls.

### 2. Serial-Boot-Marker auf Hardware

- Unit stammt aus Profil **`developer-qemu`** (QEMU-Lab-Serial-Sichtbarkeit).
- Service hatte `TTYPath=/dev/ttyS0` + `StandardOutput=tty` → auf MSI ohne QEMU-Serial **systemd-Failure**, obwohl Skript selbst tolerant ist.
- Unit war global enabled (multi-user.target.wants), läuft aber nur sinnvoll unter QEMU.

## Fix (Workspace, ISO-Rebuild ausstehend)

| Bereich | Änderung |
|---------|----------|
| Paketliste | `firmware-iwlwifi`, `firmware-intel-sound`, `wireless-regdb`, `network-manager` |
| Serial-Marker-Unit | `ConditionVirtualization=qemu`, Journal-Logging statt `TTYPath` |
| Validator | prüft Firmware-Pakete + `wireless-regdb` + QEMU-only Serial-Marker (developer-qemu) |
| Intel BT | über **`firmware-iwlwifi`** (`intel/ibt-*` in non-free-firmware); `firmware-intel-sound` nur Intel-Sound-DSP |

**Nächster Operator-Schritt:** `sudo clean` + controlled ISO rebuild (`RESCUE_MSI_FIRMWARE_REBUILD_FREIGEGEBEN=1`), Stick neu schreiben, MSI erneut booten.

## Klassifikation

- **UEFI-Boot:** `partial_success` — Live-System startet, Lab-Unit-Failure + fehlende Firmware
- **Windows-Inspect:** weiter **blockiert**
- **Telemetrie:** nicht bestätigt (WLAN ohne Firmware + NM nicht im alten Image)

## Blocker (nach Triage)

- `RESCUE_ISO_INTEL_WIFI_BT_FIRMWARE_MISSING` — bis ISO-Rebuild mit Firmware-Paketen
- `RESCUE_SERIAL_BOOT_MARKERS_HARDWARE_INCOMPATIBLE` — bis ISO-Rebuild mit QEMU-only-Condition
- `RESCUE_TARGET_NETWORK_TELEMETRY_NOT_VALIDATED`
- `WINDOWS_INSPECT_BLOCKED_UNTIL_LIVE_NETWORK_VALIDATED`

## Nächster Prompt

**`RESCUE_ISO_MSI_FIRMWARE_SERIAL_MARKER_REBUILD_OPERATOR_RUN`**

## Secrets

Keine Secrets in dieser Datei.
