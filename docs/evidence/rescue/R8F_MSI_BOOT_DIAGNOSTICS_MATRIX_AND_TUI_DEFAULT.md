# R8F — MSI: Boot-Diagnose-Matrix, TUI-Default & Treiber-Absicherung

**Version:** 1.7.19.0
**Hardware:** MSI GE63 Raider RGB 8RF, NVIDIA GTX 1070, Intel Core i7
**Anlass:** Trotz R8E-Fix (`--no-sandbox`) auf echter Hardware weiter „blinkender Cursor"
(Eintrag 1/2) bzw. Hänger nach WLAN-Meldung (Kompatibilitätsmodus). Forderung: alles auf
den Stick loggen, bevor weitergebootet wird; Treiber/WLAN absichern.

## Root Cause (warum VM grün, Hardware schwarz)

`start-assistant.service` läuft `ConditionVirtualization=!qemu` — also **nur auf echter
Hardware**, nicht in der QEMU-VM. In der VM lief der Login-/Kiosk-Pfad (grün), auf der
Hardware der **Start-Assistant auf tty1**.

Der Start-Assistant exec'te im `--boot-trigger` **direkt den grafischen Kiosk** (`ui-launch`
→ Chromium) — **ohne X-Server** (tty1 = Textkonsole):

```
exec /usr/local/sbin/setuphelfer-rescue-ui-launch   # vorher
```

- Vor R8E: Chromium-Zygote-Crash-Loop (root ohne `--no-sandbox`).
- Nach R8E: Chromium kommt an der Sandbox vorbei, scheitert dann an „kein Display" →
  beendet sich → tty1 bleibt leer = **blinkender Cursor**.

## Fixes

### 1. Boot-Diagnose-Matrix (logge alles auf den Stick, bevor es hängt)

Neu: `setuphelfer-rescue-boot-diagnostics` + 3 systemd-Units. Schreibt einen **vollständigen
Snapshot** nach `setuphelfer/diagnostics/<stamp>_<phase>/` und `.../latest/` auf den Stick:

| Datei | Inhalt |
|---|---|
| `00-meta`, `01-dmidecode`, `02-cpu-mem` | Boot-cmdline, DMI (Produkt/Board/BIOS), CPU/RAM |
| `10-lspci`, `11-lsusb`, `12-lsmod`, `13-loaded-modules-net-gpu` | Geräte + geladene Treiber |
| `20-dmesg-firmware`, `21-firmware-present` | Firmware-Ladevorgänge + vorhandene Firmware/Pakete |
| `30-dmesg-gpu`, `31-drm-status`, `32-xorg-log` | GPU/KMS (blinkender-Cursor-Ursache) |
| `40-net-links`, `41-wifi`, `42-nm-journal` | Netz/WLAN: rfkill, iw, nmcli, NetworkManager |
| `50-systemd-jobs`, `51-failed`, `52-blame`, `53-critical-chain`, `54-service-status` | **Was hängt** |
| `60-ps`, `61-rescue-run-state`, `90/91/92-journal/dmesg` | Prozesse + volle Logs |

Persistenz-Kern: live-boot mountet den Stick **read-only** unter `/run/live/medium` (deshalb
gingen bisherige Logs verloren). Der Diagnose-Logger **mountet den ESP selbst read-write**
(by-label `SETUPHELFER`, sonst `remount,rw`) und ruft `sync` — übersteht hartes Ausschalten.

Ausführung:
- `boot-diagnostics.service`: oneshot, **vor** Assistant/Kiosk/UI (`Before=`), früh.
- `boot-diagnostics.timer`: alle 15 s ein frischer Snapshot (letzter Stand vor dem Hänger).
- `boot-diagnostics-shutdown.service`: finaler Snapshot beim Herunterfahren.

Lokal verifiziert: 25 Capture-Dateien + `latest/`, valider Inhalt (DMI, list-jobs, Netz,
iwlwifi-Firmwareliste), Exit 0.

### 2. TUI als Default (kein Blank-Screen mehr)

`start-assistant`: grafischer Kiosk nur noch **opt-in** via `setuphelfer_kiosk=1` (dann über
`kiosk-start`, das X korrekt via `startx` hochfährt). Default = robustes whiptail-Text-Menü
auf tty1 — funktioniert auf jeder GPU (GTX 1070 ohne Treiber, `nomodeset`) und bietet WLAN-
Onboarding + Telemetrie.

### 3. Treiber/Firmware

Paketliste bereits breit (`firmware-iwlwifi`, `-realtek`, `-atheros`, `-brcm80211`,
`-misc-nonfree`, `network-manager`, `wpasupplicant`, `rfkill`, `iw`). Ergänzt: `dmidecode`
(Hardware-ID für Diagnose). Diagnose-Snapshot zeigt künftig exakt den WLAN-Chip + Firmware-
Status des MSI, sodass fehlende Firmware gezielt nachgezogen werden kann statt zu raten.

## Regressions-Guards (`validate-controlled-live-build-tree.sh`)

- Diagnose-Skript + 3 Units + wants/timers-Symlinks Pflicht.
- Diagnose-Skript muss ESP **rw** mounten **und** `sync`.
- `dmidecode` in Paketliste.
- `start-assistant` muss Kiosk hinter `setuphelfer_kiosk=1` gaten.

## Nachtrag (1.7.19.1): Persistenz-Bug gefixt — Stick war leer

Erster MSI-Boot mit 1.7.19.0: **nichts** auf den Stick geschrieben (kein `diagnostics/`,
alle Dateien = Schreibzeit). Ursache: `ensure_esp_rw` akzeptierte einen zweiten vfat-Mount
**ohne Schreibtest**; ein zweiter Mount erbt aber die bereits **read-only** Superblock-Instanz
(live-boot) → alle Schreibvorgänge scheiterten still → leerer Stick.

Fix:
- `_rw_usable` Schreibtest (Datei wirklich anlegbar) **vor** Akzeptanz jedes Mountpfads.
- Primär `mount -o remount,rw` des Live-Mediums (`/run/live/medium` bzw. `/lib/live/mount/medium`).
- `timeout` um `mount`/`sync`; Diagnose-Service **nicht** mehr `Before=start-assistant`
  (eine langsame Capture darf die tty1-TUI nicht verzögern → kein Schein-Hänger).
- Verifiziert: Capture schreibt + liest auf echtem FAT32-Stick, RAM-Fallback greift sauber.

## Nutzung nach dem Boot

Stick in einen funktionierenden Rechner stecken → Partition `SETUPHELFER` →
`setuphelfer/diagnostics/latest/` lesen (v. a. `50-systemd-jobs`, `54-service-status`,
`30-dmesg-gpu`, `41-wifi`). Damit ist der MSI-Hänger offline diagnostizierbar.
