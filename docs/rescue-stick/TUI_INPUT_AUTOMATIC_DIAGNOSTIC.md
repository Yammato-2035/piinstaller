# TUI Input Automatic Diagnostic (PI-RS-TUI-AUTO-001)

## Purpose

Operator-guided, largely automated diagnosis of an unresponsive Setuphelfer text menu
(`whiptail`/`newt` on tty1) without depending on those libraries for the diagnostic UI.

## Activation

Kernel cmdline (dedicated GRUB entry only):

```text
setuphelfer_tui_input_diag=1
setuphelfer_tui_input_diag_auto_shutdown=0
```

Optional: `setuphelfer_tui_input_diag_timeout=<seconds>`.

Normal boot entries are unchanged and do **not** start the diagnostic service.

## Architecture

| Component | Location |
|-----------|----------|
| GRUB entry | `rescue_msi_lab_auto_boot.ensure_tui_input_diagnostic_menuentry` / FAT32 generator |
| systemd | `setuphelfer-rescue-tui-input-diagnostic.service` → `/dev/tty2` |
| CLI | `/usr/local/sbin/setuphelfer-rescue-tui-input-diagnostic` |
| Engine | `backend/core/rescue_tui_input_diagnostic*.py` |
| TUI write guard | `setuphelfer-rescue-tui.sh` blocks e2e/plan/gui/reboot/poweroff when flag set |

Observed TUI remains on **tty1**. Diagnostic assistant runs on **tty2**.

## Safety

- No exclusive `EVIOCGRAB`, no key injection, no `kill` of TUI, no `stty sane`.
- Evidence only under SETUP_LOGS (or `/run/setuphelfer/tui-input-diagnostics` fallback).
- Auto-shutdown default **off**.

## Evidence layout

`SETUP_LOGS/tui-input-diagnostics/<RUN_ID>/` with atomic writes, manifest, SHA256SUMS.
