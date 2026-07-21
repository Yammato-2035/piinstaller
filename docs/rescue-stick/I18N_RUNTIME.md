# i18n Runtime (Rescue GUI Progress)

**Task:** PI-RS-BVR-GUI-DCC-001  
**Locales:** `de-DE`, `en-US`, `fr-FR`, `nl-NL`

## Dateien

```text
scripts/rescue-live/image/locales/de-DE.json
scripts/rescue-live/image/locales/en-US.json
scripts/rescue-live/image/locales/fr-FR.json
scripts/rescue-live/image/locales/nl-NL.json
```

Im Payload unter: `/usr/share/setuphelfer/rescue/ui/locales/`

## Auswahl

1. Umgebung: `SETUPHELFER_RESCUE_LOCALE`
2. Kernel-Cmdline: `setuphelfer_locale=de-DE` (etc.)
3. Fallback: `de-DE`

## Validierung

- **Progress-Page** (`auto-e2e-progress.html`): alle vier Locale-Dateien **Pflicht** — Launcher prüft vor Start; Health liefert `i18n_validation=passed|failed`.
- **Interaktive** `rescue.html`: Locales optional; Health setzt `i18n_required=false`.

## Phase-Labels

Zusätzlich im HTTP-Server (`PHASE_LABELS` in `setuphelfer-rescue-ui-http-server`) — ASCII-only Strings für Auto-E2E-API `/api/rescue/auto-e2e-status`.

## DCC-Status

`evaluate_i18n_status()` in `rescue_bvr_dcc_status.py`:

- `complete` — alle vier Dateien, gleiche Key-Menge
- `incomplete` — fehlende Datei oder Key-Mismatch
- `unknown` — keine Daten

## Evidence

- [RESCUE_I18N_INVENTORY.md](../evidence/rescue/bvr-gui-dcc-001/RESCUE_I18N_INVENTORY.md)
- [rescue_i18n_completeness.json](../evidence/rescue/bvr-gui-dcc-001/rescue_i18n_completeness.json)

## Siehe auch

- [I18N_RUNTIME.md](./I18N_RUNTIME.md) — diese Datei
- [RESCUE_BOOT_MENU_I18N.md](./RESCUE_BOOT_MENU_I18N.md) — GRUB-Menü (separater Scope)
