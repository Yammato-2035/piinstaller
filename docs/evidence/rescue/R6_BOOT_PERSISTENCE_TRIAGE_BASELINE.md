# R.6 — Boot / Persistence Triage Baseline

**Datum:** 2026-06-10  
**Projektversion:** 1.7.17.0  
**HEAD:** `57e30d9` (Workspace)  
**Vorgänger:** R.5C MSI Boot Evidence Review

## USB-Write (R.5B)

| Feld | Wert |
|------|------|
| Write-ID | `fat32_esp_write_20260613_171403` |
| USB Write | **OK** |
| Verify | **OK** |
| Stick-Label | `SETUPHELFER` |
| GPT-Name | `SETUPHELFER_RESCUE` |
| Evidence-Pfad | `docs/evidence/runtime-results/rescue/fat32_esp_write_20260613_171403/` |

## ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` |

## Stick-Stand am Dev-Rechner (post-write, pre-R.6-fix)

| Check | Status |
|-------|--------|
| Mount | `/media/gabriel/SETUPHELFER` |
| `/setuphelfer-evidence/` | **fehlt** |
| Write-Time `setuphelfer/rescue/evidence.json` | vorhanden |
| GRUB `set theme=` in `grub.cfg` | **yellow** (statisch) |
| RS-001 Level 6 (Hardware-Boot / Runtime-Evidence) | **rot** |
| Runtime-Evidence | **unknown/red** |

## Hypothesen-Ranking (vor R.6-Fix)

| ID | Szenario | Einstufung |
|----|----------|------------|
| D | TUI/Kiosk startet, Evidence nicht auf Stick | **wahrscheinlich** (kein früher Hook) |
| E | Evidence nur in RAM (`/tmp/setuphelfer-evidence`) | **möglich** (FAT ro / Fallback) |
| F | Stick-Persistenz falsch erkannt | **möglich** |
| A–C | MSI bootet nicht / GRUB / Linux hängt | **unbekannt** (Operator-Beobachtung fehlt) |

## Klassifikation (vorläufig)

`menu_loaded_no_persistence` — Stick-Inhalt bootfähig, Runtime-Baum `/setuphelfer-evidence/` fehlt.

## Nächster Schritt

R.6 Hook `setuphelfer-rescue-boot-evidence-init` → Rebuild → Stick-Write (Operator) → MSI-Boot → Prüfung `setuphelfer-evidence/boot/boot_marker.md`.
