# ASUS-00 headless / F2-Kommandozeile — Root Cause

Stand: 2026-08-07

## Beobachtung

Boot endet ohne Setuphelfer-TUI; Operator sieht eine bare Kommandozeile („F2“).

## Ursache

ASUS-Menüeinträge auf dem FAT32-ESP enthielten **kein** `setuphelfer_start_assistant=1`.

`setuphelfer-rescue-start-assistant.service` ist gated mit:

`ConditionKernelCommandLine=setuphelfer_start_assistant=1`

Ohne diesen Parameter startet der Assistent/TUI nicht. Das Live-System bleibt auf einer
normalen Textkonsole stehen (wirkt „headless“).

Zusätzlich beendet `setuphelfer-rescue-entrypoint.sh` bei `--boot-trigger` ohne
`setuphelfer_start_assistant=1` sofort mit `exit 0`.

## Fix

1. `generate_fat32_esp_grub_cfg` / ISO-/Isolinux-Snippets: ASUS-Profile inkl. `setuphelfer_start_assistant=1`
2. ESP `grub.cfg` auf dem physischen Stick hot-gepatcht (kein Full-Rewrite)
3. Erneuter ASUS-00-Boot erforderlich

## Nicht ursächlich

- Kein Hinweis auf NVMe-/Windows-Schreiben
- SquashFS/Sentinels waren vorhanden; Problem war Bootparameter → Service-Gate
