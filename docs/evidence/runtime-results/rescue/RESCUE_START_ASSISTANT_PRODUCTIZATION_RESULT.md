# RESCUE_START_ASSISTANT_PRODUCTIZATION — Ergebnis

**Datum:** 2026-06-07  
**HEAD vorher:** `d76e3ef`  
**Version vorher → nachher:** `1.7.6.0` → **`1.7.7.0`**

## Phase 0

| Feld | Wert |
|------|------|
| Runtime-Drift | Workspace `1.7.7.0` vs API `1.7.4.1` (Warnung) |
| Letzte ISO | `80508492…` (1.7.6.0) — **nicht** mit 1.7.7.0 gebaut |
| Keine schreibenden Runtime-Aktionen | ja |

## Umgesetzt (Workspace)

### Boot-Branding / Menü
- **Root Cause alter Hook:** falsche ISOLINUX-Syntax (`LABEL`/`LINUX` statt `label`/`kernel`)
- Fix: `live.cfg.in`-Snippet + korrigierter Binary-Hook + `MENU TITLE Setuphelfer Rettungsstick`
- Menüeinträge: Rettung starten, Netzwerk-Assistent, MSI/NVIDIA-Kompat, Diagnose, toram/Media-Check, Neustart, Herunterfahren

### WLAN-Onboarding
- Index-basierte SSID-Auswahl (kein Tag=SSID-Bug)
- `--passwordbox` für Passwort (nicht geloggt)
- Verstecktes WLAN, Rescan, Offline-Modus (Exit 20, Telemetrie-Spool)
- OK/Return bricht nicht ab (`set -uo` ohne `-e` in Onboarding)

### Telemetrie
- Weiterhin separates Python-Payload-Modul (kein Inline-Heredoc)
- Auto-Push nach Route+Health; Spool + Retry-Timer

### Live-Media-Check
- SquashFS-Lesetest + Spot-Checks (nmcli, curl, telemetry, branding, start-assistant)
- Blockiert Reparatur/Install-Pläne bei Instabilität

### Disk-Discovery (read-only)
- `setuphelfer-rescue-disk-discovery.py` — lsblk-Klassifikation: rescue_stick, backup_disk, windows/linux, EFI, …
- Keine rw-Mounts

### Start Assistant (TUI)
- `setuphelfer-rescue-start-assistant` — Wizard: Willkommen → Media → Netzwerk → Telemetrie → Disks → Empfehlung → Hauptmenü
- `RescueWizardState` JSON (`wizard-state.json`) — GUI-ready
- `setuphelfer-rescue-plan-builder.py` — Backup/Restore/Repair/Install **nur Pläne**, `execution_allowed: false`

## Tests

```
python3 -m unittest backend.tests.test_rescue_start_assistant_v1 backend.tests.test_rescue_live_telemetry_scripts_v1
→ 15/15 OK
```

## Build / ISO

| Schritt | Ergebnis |
|---------|----------|
| `prepare-controlled-live-build-tree.sh` | **OK** |
| `validate-controlled-live-build-tree.sh` | **BLOCKIERT** — root-owned stale `chroot/` (Operator: `sudo clean-controlled-live-build-tree.sh`) |
| ISO-Rebuild | **nicht durchgeführt** |
| USB-Rewrite | **nicht freigegeben** |

## Was im ISO ist vs. Workspace

| | Alte ISO `80508492…` | Workspace 1.7.7.0 |
|---|---|---|
| Start Assistant | nein | **ja** (Build-Tree) |
| Boot-Menü live.cfg.in | nein | **ja** |
| WLAN passwordbox fix | nein | **ja** |
| Disk discovery | nein | **ja** |

## Blocker (ehrlich)

- `RESCUE_ISO_REBUILD_REQUIRED_FOR_START_ASSISTANT_1_7_7_0`
- `RESCUE_USB_REWRITE_BLOCKED_UNTIL_ISO_VALIDATED`
- `RESCUE_MSI_BOOT_AUTOMATED_TELEMETRY_ACK_PENDING`
- `WINDOWS_INSPECT_BLOCKED`

## Nächster Prompt

**`RESCUE_START_ASSISTANT_ISO_REBUILD_OPERATOR_COMPLETION`**
