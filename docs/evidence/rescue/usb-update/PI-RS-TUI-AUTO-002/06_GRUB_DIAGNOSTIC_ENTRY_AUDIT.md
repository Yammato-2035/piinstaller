# 06 – GRUB Diagnostic Entry Audit

Methode: `ensure_tui_input_diagnostic_menuentry` (kein Full-Rewrite der Lab-Einträge).

| GRUB-Eintrag | Vorher | Neu | Erwartete Änderung |
|--------------|--------|-----|--------------------|
| Lab-Auto (GUI, Backup/Verify) default=0 | vorhanden | vorhanden | **keine** |
| Lab-Auto (Text, Backup/Verify) | vorhanden | vorhanden | **keine** |
| Standard GUI / Text | vorhanden | vorhanden | **keine** |
| TUI-Eingabediagnose (read-only) | fehlte | **neu** Index 7 | hinzugefügt |
| set default=0 | ja | ja | **keine** |

Diagnose-Flags: `mode=text`, `setuphelfer_tui_input_diag=1`, `setuphelfer_tui_input_diag_auto_shutdown=0`, MSI nouveau blacklist.

| Hash | Wert |
|------|------|
| GRUB vorher | `c8fa330c65659b2db872ab0ea1f6336ee51d0d0e2cc57103d21761a4c6478ef6` |
| GRUB geplant | `68649d4dab94a19c4ead0acbe060902d215fb36b4b13ffa5ef27d9f195931030` |
