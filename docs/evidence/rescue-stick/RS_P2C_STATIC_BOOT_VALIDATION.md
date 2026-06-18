# RS-P2C Static Boot Validation

## GRUB (Workspace-Generator)

| Check | Status |
|-------|--------|
| 7 menuentry | pass |
| Default Textmodus | pass |
| GUI optional (kiosk=1 nur GUI-Eintrag) | pass |
| timeout_style=menu, timeout=15 | pass |
| Kein Theme-Default | pass |

## Squashfs 1.9.5.2

| Artefakt | Im Squashfs |
|----------|-------------|
| setuphelfer-rescue-entrypoint | ja |
| setuphelfer-rescue-tui | ja |
| setuphelfer-rescue-gui-watchdog | ja |
| collect-rescue-runtime-diagnostics | ja |
| Backend rescue_boot_* contracts | ja (via rsync) |

## QEMU

Nicht in diesem Lauf ausgeführt — kein MSI-Ersatz.
