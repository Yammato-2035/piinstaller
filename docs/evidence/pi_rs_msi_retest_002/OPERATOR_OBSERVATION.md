# PI-RS-MSI-RETEST-002 — Operator-Beobachtung

**Datum:** 2026-07-12, ca. 11:12 Uhr (Session `20260712_111206_boot`)  
**Testgerät:** MSI GE63 Raider RGB 8RF / MS-16P5  
**Operator-Meldung:** Text-GUI (TUI) wurde **wieder zerstört**

## Boot

| Feld | Wert |
|------|------|
| Session | `20260712_111203_early` + `20260712_111206_boot` |
| Kernelparameter | `setuphelfer_msi_compat=1 nomodeset nouveau.modeset=0 pci=noaer` |
| Modus | `setuphelfer_mode=text`, `setuphelfer_kiosk=0` |
| Produkt | GE63 Raider RGB 8RF / MS-16P5 |

## TUI

| Feld | Wert |
|------|------|
| TUI gestartet | ja (laut Boot, dann zerstört) |
| TUI stabil | **nein** — Operator: visuelle Zerstörung |
| Visuelle Auffälligkeiten | Whiptail/Textoberfläche unbrauchbar |

## GUI / MSI-Compat

| Feld | Evidence |
|------|----------|
| `gui-availability.json` | `gui_available=false`, `reason=msi_compat_nomodeset` |
| `gui-fallback.json` | `openvt_attempted=false`, `startx_attempted=false` |
| `boot-timeline.jsonl` 11:12:22 | Phase **`x11_starting`** — „Grafische Oberfläche wird gestartet …“ |
| `rescue-ui-status.json` | Stale: `openvt_console_2_not_released` (Session 01:59) |
| `gui-start.log` | Kein neuer Eintrag für 11:12 — letzter OPENVT von 01:59 |

## Versionen

| Quelle | Version |
|--------|---------|
| SETUPHELFER `version.json` (ESP) | **1.10.0.15** |
| SquashFS SHA256 | `307ae9a3…` (korrekt) |
| Runtime `/api/version` + `config/version.json` im SquashFS | **1.10.0.12** (Drift!) |

## Sicherheit

- Keine Backup/Restore/Wipe-Aktionen
- Interne Platten nicht beschrieben (nur Lesen)

## Bewertung

**`failed`** — TUI erneut optisch zerstört trotz PI-RS-MSI-GUI-002 Payload.

Verdacht:

1. Boot-Progress zeigt weiterhin `x11_starting` unter MSI-Compat (tty1-Konflikt).
2. `console-shield` blockiert `tty1_clear_allowed` während `early_boot_progress`.
3. Runtime-Version im SquashFS noch **1.10.0.12** — Repack/Updater-Sync unvollständig.
