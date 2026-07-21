# GRUB and boot audit

| Entry | 1.10.0.59 | 1.10.0.60 | Assessment |
|-------|-----------|-----------|------------|
| Standard (default=0 GUI lab) | present | present | unchanged |
| Text mode | present | present | unchanged |
| TUI-Eingabediagnose | present | present | unchanged |
| `setuphelfer_tui_input_diag=1` | only diag entry | only diag entry | OK |
| `setuphelfer_tui_input_diag_auto_shutdown=0` | yes | yes | OK |
| GRUB SHA256 | `68649d4dab94a19c4ead0acbe060902d215fb36b4b13ffa5ef27d9f195931030` | `68649d4dab94a19c4ead0acbe060902d215fb36b4b13ffa5ef27d9f195931030` | identical |
| Kernel / Initrd | unchanged | unchanged | OK |
