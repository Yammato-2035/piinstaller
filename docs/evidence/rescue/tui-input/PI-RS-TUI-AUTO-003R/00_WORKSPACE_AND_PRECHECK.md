# Workspace and precheck

## Workspace
- Path: `/home/volker/piinstaller`
- Branch: `pi-rs-e2e-live-001d-physical-backup-restore`
- HEAD: `1d4b82af`
- origin/main: `b8651d3337bf30b4443a622fdf8a6c9dc2995df5`
- Ancestors: `3d494424` (fix), `72fb66d5` (EVIDENCE-002) present
- Drift: foreign dirty files present; left untouched

## Stick identification
- Device: `/dev/sda`
- Model: Intenso Ultra Line
- TRAN=usb, RM=1, ~59G
- Partitions: SETUPHELFER (`sda1`), SETUP_LOGS (`sda2`)
- Root disk: `/dev/nvme0n1` (not target)

## Payload verification (read-only)
| Artifact | Expected | Actual | OK |
|----------|----------|--------|----|
| Payload version | 1.10.0.60 | 1.10.0.60 | yes |
| GRUB | 68649d4d… | 68649d4d… | yes |
| Kernel | d8deb726… | d8deb726… | yes |
| Initrd | 385dd4f1… | 385dd4f1… | yes |
| SquashFS | ee17958c… | ee17958c… | yes |
| Diag GRUB entry | present, not default | yes (`default=0` = Lab GUI) | yes |
| Auto-shutdown diag | 0 | present | yes |
| Persistence module in squash | present | `rescue_tui_input_diagnostic_persistence.py` + unit | yes |

## SETUP_LOGS before run
- `tui-input-diagnostics/` **absent** (no prior persistent diagnostic run)
- Other content under `setuphelfer/` present (not deleted)

## Preboot status
`preboot_ok` — MSI boot may proceed after safe unmount.
