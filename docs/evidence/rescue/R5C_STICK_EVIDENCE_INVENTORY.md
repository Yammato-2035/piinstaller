# R.5C — Stick Evidence Inventory

**Datum:** 2026-06-13  
**Mount:** `/media/gabriel/SETUPHELFER` (read-write user mount, **nur Auswertung**)  
**Methode:** `find` auf Stick-Root

## Runtime-Baum `/setuphelfer-evidence/`

| Check | Status |
|-------|--------|
| `setuphelfer-evidence/` vorhanden | **nein** |

## Verzeichnisse (erwartet nach MSI-Boot)

| Verzeichnis | Status |
|-------------|--------|
| boot/ | **fehlt** |
| menu/ | **fehlt** |
| hardware/ | **fehlt** |
| network/ | **fehlt** |
| telemetry/ | **fehlt** |
| rescue-ui/ | **fehlt** |
| matrix/ | **fehlt** |
| summaries/ | **fehlt** |

## Pflichtdateien

| Datei | Status |
|-------|--------|
| matrix/rescue_test_matrix_latest.md | **fehlt** |
| matrix/rescue_test_matrix_latest.json | **fehlt** |
| matrix/rescue_test_matrix_history.jsonl | **fehlt** |
| summaries/rescue_evidence_latest.md | **fehlt** |
| summaries/rescue_evidence_latest.json | **fehlt** |
| hardware/msi_diagnostics_latest.md | **fehlt** |
| hardware/msi_diagnostics_latest.json | **fehlt** |

## Vorhanden (Write-Time, nicht MSI-Runtime)

| Pfad | Typ |
|------|-----|
| `EFI/BOOT/BOOTX64.EFI` | Bootloader |
| `boot/grub/grub.cfg` | GRUB config |
| `boot/grub/themes/setuphelfer/*` | Theme |
| `live/vmlinuz`, `live/initrd.img`, `live/filesystem.squashfs` | Live payload |
| `setuphelfer/rescue/evidence.json` | Writer evidence |
| `setuphelfer/rescue/version.json` | Version stamp |
| `setuphelfer/rescue/boot-branding.txt` | Branding |

## Klassifikation

| Ursache-Hypothese | Wahrscheinlichkeit |
|-------------------|-------------------|
| **MSI-Boot nicht erreicht / nicht durchgeführt** | hoch |
| Stick nicht beschreibbar zur Laufzeit | mittel (FAT rw mount am Dev-Rechner OK) |
| Evidence-Skript nicht gestartet | mittel (erfordert erfolgreichen Live-Boot) |
| Persistenzpfad nicht erkannt | mittel |
| TUI/Kiosk nicht gestartet | folgt aus fehlendem Boot |

## Ampel Inventory

**rot** — Runtime-Evidence-Pflichtset fehlt vollständig.
