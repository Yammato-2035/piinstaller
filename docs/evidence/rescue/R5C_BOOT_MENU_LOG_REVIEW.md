# R.5C — Boot / Menu Log Review

**Datum:** 2026-06-13

## Datenlage

**Keine Boot-/Menü-Logs auf Stick** (`setuphelfer-evidence/boot/`, `menu/` fehlen).

## Statische Stick-Analyse (pre-boot)

Aus `boot/grub/grub.cfg` auf Stick (read-only):

| Feld | Befund |
|------|--------|
| FAT root search | `search --fs-uuid FE8C-7F79` + Label-Fallback `SETUPHELFER` |
| Theme | **`set theme=($root)/boot/grub/themes/setuphelfer/theme.txt`** — vorhanden |
| gfxterm/png | insmod vorhanden |
| Default menuentry | „Setuphelfer Rettung starten“ |
| kernel cmdline (default) | `boot=live components quiet setuphelfer_rescue=1 setuphelfer_start_assistant=1` |
| MSI compat entry | `setuphelfer_msi_compat=1`, `nomodeset`, `nouveau.modeset=0` |
| initrd | `/live/initrd.img` |

## Runtime-Felder (nicht verfügbar)

| Prüfpunkt | Status |
|-----------|--------|
| Boot context | **fehlt** |
| Kernel cmdline (actual) | **fehlt** |
| UEFI erkannt | **unbekannt** |
| Secure Boot Hinweis | **unbekannt** |
| Live-Medium erkannt | **unbekannt** |
| Stick-Persistenz erkannt | **unbekannt** |
| TUI gestartet | **unbekannt** |
| Kiosk gestartet | **unbekannt** |
| Browser gefunden | **unbekannt** |
| Display gefunden | **unbekannt** |
| Fehler/Tracebacks | **keine Logs** |
| Menü-Abbrüche | **keine Logs** |
| WLAN-Rescan-Fehler | **keine Logs** |

## Operator-Notizen (MSI-Boot)

*Auszufüllen nach manuellem MSI-Boot (Phase 1 Checklist):*

- GRUB: grafisch / Text / kein Menü?
- Linux startet: ja/nein?
- Hänger/Fehlertext?

## Bewertung

**rot** — Boot-Logs fehlen; statisches GRUB-Layout auf Stick **yellow/green**.
