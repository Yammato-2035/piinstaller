# R.6 — Stick Static Self-Check

**Datum:** 2026-06-10  
**Mount:** `/media/gabriel/SETUPHELFER`  
**Methode:** Read-only Dateiprüfung am Dev-Rechner (kein USB-Write)

## Pflichtdateien

| Pfad | Status |
|------|--------|
| `EFI/BOOT/BOOTX64.EFI` | **FOUND** |
| `boot/grub/grub.cfg` | **FOUND** |
| `boot/grub/themes/setuphelfer/theme.txt` | **FOUND** |
| `live/vmlinuz` | **FOUND** |
| `live/initrd.img` | **FOUND** |
| `live/filesystem.squashfs` | **FOUND** |
| `setuphelfer/rescue/evidence.json` | **FOUND** |
| `setuphelfer/rescue/version.json` | **FOUND** |
| `setuphelfer-evidence/` | **MISSING** |

## GRUB / Kernel

| Prüfung | Ergebnis |
|---------|----------|
| `search --label SETUPHELFER` | **ja** (korrektes Label) |
| `linux` → `/live/vmlinuz` | **ja** (FAT32-relative Pfade) |
| `initrd` → `/live/initrd.img` | **ja** |
| `setuphelfer_start_assistant=1` (Default-Menü) | **ja** |
| `setuphelfer_rescue=1` | **ja** |
| dedizierte `evidence`/`persistent` cmdline-Parameter | **nein** (Erkennung zur Laufzeit via Mount) |
| `set theme=($root)/boot/grub/themes/setuphelfer/theme.txt` | **ja** → GRUB static **yellow** |

## Mechanismus `/setuphelfer-evidence` auf FAT32

| Mechanismus | Vor R.6-Fix | Nach R.6-Fix (geplant) |
|-------------|-------------|------------------------|
| USB-Writer legt Runtime-Baum an | **nein** | **nein** (nur Live-Boot) |
| `setuphelfer-rescue-boot-evidence-init` | **fehlt im Image** | **ja** (Start-Assistent Anfang) |
| `setuphelfer-rescue-evidence.py bundle` | Ende Assistent | unverändert |
| Legacy `mirror_evidence_file` → `setuphelfer/evidence/` | **ja** | parallel, nicht kanonisch |

## Fazit Static Check

Stick ist **bootfähig** und enthält vollständiges Live-Payload. Fehlender `/setuphelfer-evidence/`-Baum ist **erwartbar vor erstem Live-Boot** und bestätigt R.5C-Befund — kein Hinweis auf defekten Write.
