# PI-RS-MSI-RETEST-002 — Operator-Beobachtung

**Status:** Physischer Boot-Retest **noch nicht durchgeführt** (Agent-Lauf, 2026-07-12).

## Vorprüfung am Entwicklungsrechner (abgeschlossen)

| Prüfung | Ergebnis |
|---------|----------|
| Git HEAD | `dfcc583d` |
| Stick identifiziert | Intenso Ultra Line, `/dev/sda` |
| Payload-Version | **1.10.0.15** |
| Payload-SHA256 | `307ae9a381e2792fddd2ca8ebb6c20550544f0b167e2461c323c596651ecd318` |
| SETUP_LOGS vor Boot | 936 Dateien inventarisiert |
| Neueste Session vor Boot | `20260712_015835` (vor 1.10.0.15-Update) |

## Operator — nach physischem GE63-Boot ausfüllen

| Feld | Wert |
|------|------|
| Datum/Uhrzeit | _ausfüllen_ |
| Testgerät | MSI GE63 Raider RGB 8RF / MS-16P5 |
| Payload-Version (sichtbar/API) | _1.10.0.15 erwartet_ |
| Bootprofil | `setuphelfer_msi_compat=1 nomodeset nouveau.modeset=0 pci=noaer` |
| TUI gestartet | ja / nein |
| TUI stabil (≥2 min) | ja / nein |
| Visuelle Auffälligkeiten | _beschreiben_ |
| GUI-Menüstatus | deaktiviert / blockiert / Meldung |
| Genaue GUI-Meldung | _wörtlich notieren_ |
| Verhalten nach GUI-Wunsch | TUI neu gerendert? ja/nein |
| `openvt`/`chvt`/`startx` beobachtet | ja/nein |
| Shutdown über Menü | ja/nein |
| Gefährliche Aktionen | nein (erwartet) |

## Runbook

`docs/evidence/pi_rs_usb_msi_gui_002/MSI_GE63_BOOT_RETEST_RUNBOOK.md`

## Nach dem Boot

1. Stick am Entwicklungsrechner einstecken
2. Neue SETUP_LOGS-Session importieren nach `docs/evidence/pi_rs_msi_retest_002/msi_session/`
3. `PI_RS_MSI_RETEST_002_ACCEPTANCE.json` und `PI_RS_MSI_RETEST_002_RESULT.md` aktualisieren
4. Commit: `Document MSI payload 1.10.0.15 physical boot retest`
