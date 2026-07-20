# 06 systemd Integration

Unit: `setuphelfer-rescue-tui-input-diagnostic.service`

- `ConditionKernelCommandLine=setuphelfer_tui_input_diag=1`
- `TTYPath=/dev/tty2`
- `Conflicts=getty@tty2.service`
- `After=` / `Wants=` `setuphelfer-rescue-tui.service`
- `Restart=no`
- Does not touch tty1 getty beyond existing TUI ownership
