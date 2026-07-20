# 05 GRUB Integration

- Title: `Setuphelfer – TUI-Eingabediagnose (read-only)`
- Appended via `ensure_tui_input_diagnostic_menuentry` (no preamble/default rewrite alone)
- Interactive patch calls ensure after placing GUI/Text defaults
- FAT32 generator adds entry before MSI-compat (default remains index 0)
- Flags: `setuphelfer_tui_input_diag=1`, `setuphelfer_tui_input_diag_auto_shutdown=0`
- Hybrid GPU flags match text interactive entry
