# PI-RS-MSI-AUTO-EVIDENCE-001 — Vollautomatisierter MSI-Lab-Boot

**Payload:** **1.10.0.20** · **Status:** **passed** (Session `20260713_003100_boot`)  
Workspace `project_version` bleibt 1.9.x — getrennter Rescue-Payload-Track

## Ziel

Keine manuelle GRUB-Auswahl, kein vorzeitiger Collector, kein manuelles Herunterfahren:

1. Stick bootet automatisch in **MSI/NVIDIA Kompatibilitaetsmodus (Text)**
2. **≥120 s** nach Boot: Spät-Evidence + RS-011B-Collect
3. Fehler werden in `lab-auto-result.json` bewertet
4. Rechner fährt automatisch herunter (`setuphelfer_auto_shutdown=1`)
5. Nach Import zeigt **Setuphelfer Cloudserver Edition** anonymisierte Daten

## Einmalig — Entwicklungsrechner

```bash
./scripts/rescue-live/repack-rescue-squashfs-react-shell.sh
./scripts/rescue/configure-stick-msi-lab-auto-grub.sh /media/$USER/SETUPHELFER
# Payload atomar: PI-RS-USB-UPDATER-001 (update-fat32-esp-live-payload.sh)
```

## Einmalig — MSI Laptop

1. Nur Setuphelfer-Stick einstecken
2. UEFI-Boot vom Stick — **keine Taste drücken** (3 s Countdown)
3. Warten **~2,5 min** — System sammelt Evidence und fährt runter

## Nach dem Boot — Entwicklungsrechner

```bash
./scripts/rescue/import-msi-rs011b-evidence.sh /media/$USER/SETUP_LOGS
```

Import akzeptiert SETUP_LOGS-Mount oder direkten `msi-rs011b`-Pfad.

## Erfolgskriterien (`lab-auto-result.json`)

| Feld | Erwartung |
|------|-----------|
| `capture_uptime_s` | ≥ 120 |
| `console_owner` | `tui` |
| `capture_after_120s` | true |
| `manual_late_evidence_file_present` | true |
| `result_status` | `passed` |
| `boot_state` Phase | `auto_shutdown_evidence_complete` |

Hinweis: `tui_mode_selected_in_timeline` kann fehlen — unter `lab_auto_unattended` nur Warnung.

## Siehe auch

- [PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md](../evidence/pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md)
- [PI_RS_MSI_AUTO_EVIDENCE_001.md](../rescue-stick/PI_RS_MSI_AUTO_EVIDENCE_001.md)
