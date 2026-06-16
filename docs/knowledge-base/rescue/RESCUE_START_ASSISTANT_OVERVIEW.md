# Setuphelfer Rettungsstick — Start Assistant (Überblick)

**Stand:** 2026-06-07 · **Version (Workspace):** `1.7.7.0` · **Commit:** `745eb2f`

Kuratierte Zusammenfassung der Produktisierung: vom Einzelscript-Stack zum geführten Rettungsstick für Anfänger — **ohne automatische Schreibaktionen** auf Zielplatten.

---

## Was sich geändert hat (Chronologie)

| Version | Schwerpunkt |
|---------|-------------|
| `1.7.5.0` | Network-Onboarding, Telemetrie-Push (erstes Design), Boot-Menü-Hook (fehlerhafte ISOLINUX-Syntax) |
| `1.7.6.0` | Telemetrie-Payload als separates Python-Modul (SyntaxError-Fix), Spool/Retry, Telemeterie-Automatisierung |
| **`1.7.7.0`** | **Start Assistant (TUI)**, read-only Disk-Discovery, Aktions-**Pläne**, robustes WLAN-Menü, Boot-Menü in `live.cfg.in` |

**Aktuelle ISO im Tree (noch 1.7.6.0):** SHA256 `80508492…` — Rebuild mit 1.7.7.0 ausstehend.

---

## Architektur (Boot → Assistent)

```text
Boot (ISOLINUX/GRUB)
  → systemd: media-check
  → systemd: network-onboarding (--boot-trigger, auto)
  → systemd: telemetry-push (+ retry timer)
  → systemd: start-assistant (tty1, kein QEMU)
  → WizardState JSON unter /run/setuphelfer-rescue/
```

---

## Komponenten

| Script / Unit | Funktion |
|---------------|----------|
| `setuphelfer-rescue-start-assistant` | Geführter TUI-Wizard (whiptail) |
| `setuphelfer-rescue-network-onboarding` | WLAN/LAN, Passwort via `--passwordbox`, Offline-Spool |
| `setuphelfer-rescue-telemetry-push` | Health + Ingest, Payload-Hash, kein Inline-Python |
| `setuphelfer-rescue-telemetry-retry.timer` | Spool erneut senden |
| `setuphelfer-rescue-media-check` | SquashFS + Spot-Reads kritischer Dateien |
| `setuphelfer-rescue-disk-discovery.py` | Read-only lsblk-Klassifikation |
| `setuphelfer-rescue-plan-builder.py` | Backup/Restore/Repair/Install **nur als Plan** |

---

## WizardState (GUI-ready)

Datei: `/run/setuphelfer-rescue/wizard-state.json`

Schema und Felder: [RESCUE_START_ASSISTANT_WIZARD_STATE.md](../../rescue-stick/RESCUE_START_ASSISTANT_WIZARD_STATE.md)

`write_actions_allowed` ist in v1 **immer `false`**.

---

## Boot-Menü (Fix 1.7.7.0)

**Root Cause alter fehlender Menüeinträge:** Binary-Hook nutzte ISOLINUX-Großschreibung (`LABEL`/`LINUX`) statt Debian-`label`/`kernel`.

**Fix:**

1. Snippet in `scripts/rescue-live/image/setuphelfer-rescue-boot-menu-snippet.cfg` → angehängt an `live.cfg.in` beim Prepare
2. Korrigierter Hook `020-setuphelfer-rescue-boot-menu.hook.binary`
3. `MENU TITLE Setuphelfer Rettungsstick` in `isolinux.cfg`

Menüeinträge: Rettung starten, Netzwerk-Assistent, MSI/NVIDIA-Kompat, Diagnose, toram/Media-Check, Neustart, Herunterfahren.

---

## Telemetrie (Developer-Laptop)

| Endpoint | Standard |
|----------|----------|
| LAN-Proxy | `http://192.168.178.140:8001` |
| Health | `/api/rescue/telemetry/health` |
| Ingest | `/api/rescue/telemetry/v1/ingest` |

Proxy ist **allowlist-only** — `/api/version` und `/openapi.json` liefern bewusst **404**.

Optional vor Boot: `SETUPHELFER_RESCUE_TELEMETRY_BIND=192.168.178.140 ./scripts/rescue-live/start-rescue-telemetry-lan-proxy.sh`

WLAN-Konfiguration ohne Repo-Secrets: USB-Ordner `SETUPHELFER_RESCUE_CONFIG/network.env` (Beispiel im Build-Tree).

---

## Sicherheitsregeln (Produkt)

- Disk-Discovery und Pläne: **read-only**
- Kein Backup/Restore/Repair/Install **ohne** Operator-Freigabe + Bestätigungsphrase (Pläne blockieren Ausführung)
- Reparatur/Installation blockiert bei instabilem Live-Medium (`media-check`)
- Rettungsstick wird als `rescue_stick` klassifiziert — **nie** als Restore-Ziel vorgeschlagen
- Windows-Inspect bleibt gesperrt bis Boot + Netzwerk + echter Telemetrie-ACK

---

## Evidence & Gates

| Dokument | Inhalt |
|----------|--------|
| [RESCUE_START_ASSISTANT_PRODUCTIZATION_RESULT.md](../../evidence/runtime-results/rescue/RESCUE_START_ASSISTANT_PRODUCTIZATION_RESULT.md) | Workspace-Ergebnis 1.7.7.0 |
| [rescue_start_assistant_latest.json](../../evidence/runtime-results/rescue/rescue_start_assistant_latest.json) | Gate-Snapshot |
| [rescue_iso_usb_gate_status_latest.json](../../evidence/runtime-results/rescue/rescue_iso_usb_gate_status_latest.json) | ISO/USB/Telemetrie-Gates |

**Nächster Operator-Prompt:** `RESCUE_START_ASSISTANT_ISO_REBUILD_OPERATOR_COMPLETION`

---

## Operator — ISO-Rebuild (Kurz)

```bash
sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live
export RESCUE_START_ASSISTANT_REBUILD_FREIGEGEBEN=1
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

Danach: USB-Rewrite + MSI-Retest (`RESCUE_MSI_BOOT_AUTOMATED_TELEMETRY_ACK_OPERATOR_RUN`).
