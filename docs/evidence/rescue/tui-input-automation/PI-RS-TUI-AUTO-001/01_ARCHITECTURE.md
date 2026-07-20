# 01 Architecture

See `docs/rescue-stick/TUI_INPUT_AUTOMATIC_DIAGNOSTIC.md`.

```
GRUB diag entry (not default)
  → cmdline setuphelfer_tui_input_diag=1 + mode=text
  → tui.service owns tty1 (normal menu)
  → tui-input-diagnostic.service owns tty2
       → Python engine (stdlib)
       → SETUP_LOGS evidence + hypothesis decision
```
