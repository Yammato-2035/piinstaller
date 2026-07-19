# PI-RS-MSI-GUI-003 — Implementation

## Änderungen

### Zentrales Bootprofil
- `backend/core/rescue_msi_boot_profile.py` — `resolve_rescue_boot_profile()` liefert `boot_mode=tui_only` unter MSI-Compat.

### Boot-Timeline
- `backend/core/rescue_boot_timeline.py` — Phasenplanung ersetzt `x11_starting` durch `tui_mode_selected`; CLI `plan`, `record`, `simulate`, `summary`.

### Console Ownership
- `backend/core/rescue_console_ownership.py` — tty1-Besitz `boot_progress` → `tui_owned`; Audit `RESCUE_CONSOLE_WRITE_BLOCKED_TUI_OWNED`.

### Session-Isolation
- `backend/core/rescue_session_evidence.py` — `init_boot_session()`, Stale-Erkennung, `/run/setuphelfer/sessions/<id>/`.

### Versionsträger
- `backend/core/rescue_payload_version_carriers.py` — synchrones `version.json` + `rescue_payload_version.json`.
- `repack-rescue-squashfs-react-shell.sh` schreibt beide beim Repack.

### Shell
- `setuphelfer-rescue-boot-progress` — Python-Plan, kein MSI `x11_starting`, Write-Guards.
- `setuphelfer-rescue-common.sh` — Session-Init, Ownership, `tty1_write_allowed`, Stale-Mirror-Guard.
- `setuphelfer-rescue-tui.sh` — Ownership-Übergabe `tui_initializing` → `tui_owned`.

### Version
- `1.10.0.15` → `1.10.0.16`

## Nicht geändert
- USB-Updater, Telemetrie-Server, Safety-Gates, GUI unter MSI (bleibt gesperrt).

## Dokumentation (2026-07-12)

| Artefakt | Pfad |
|----------|------|
| Sprint-Zusammenfassung | [PI_RS_MSI_GUI_003_SUMMARY.md](PI_RS_MSI_GUI_003_SUMMARY.md) |
| Operator-Runbook | [PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md](../../rescue-stick/PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md) |
| FAQ DE / EN | [PI_RS_MSI_GUI_003_FAQ.de.md](../../faq/PI_RS_MSI_GUI_003_FAQ.de.md), [PI_RS_MSI_GUI_003_FAQ.en.md](../../faq/PI_RS_MSI_GUI_003_FAQ.en.md) |
| Wissensdatenbank | [MSI_TUI_CONSOLE_ISOLATION_KB_DE.md](../../knowledge-base/rescue/MSI_TUI_CONSOLE_ISOLATION_KB_DE.md), [MSI_TUI_CONSOLE_ISOLATION_KB_EN.md](../../knowledge-base/rescue/MSI_TUI_CONSOLE_ISOLATION_KB_EN.md) |
| i18n (Doku-JSON) | [rescue_boot_msi_compat_DE.json](../../i18n/rescue_boot_msi_compat_DE.json), [rescue_boot_msi_compat_EN.json](../../i18n/rescue_boot_msi_compat_EN.json) |
| Rescue-UI i18n | `frontend/src/rescue/i18n/{de,en,fr,nl}.json` → `boot.msiCompat.*`, `evidence.msiStaleSession`, `evidence.msiTuiOnlyMode` |
| MSI-Evidence-FAQ | Ergänzt in [RESCUE_MSI_EVIDENCE_FAQ_DE.md](../../faq/RESCUE_MSI_EVIDENCE_FAQ_DE.md) / EN |
