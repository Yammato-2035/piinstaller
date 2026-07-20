# 03 Safety Analysis

| Rule | Status |
|------|--------|
| No EVIOCGRAB / uinput / key injection | enforced (static test) |
| No kill/restart of TUI | enforced |
| No stty sane / reset | not implemented |
| No backup/restore/partition | TUI guard blocks e2e/plan/gui/reboot/poweroff |
| Evidence path restricted | SETUP_LOGS or `/run/setuphelfer` |
| Auto-shutdown default off | yes |
| Normal boot path unchanged | diag only with cmdline flag; GRUB default=0 unchanged |
| USB write | not performed in this phase |
