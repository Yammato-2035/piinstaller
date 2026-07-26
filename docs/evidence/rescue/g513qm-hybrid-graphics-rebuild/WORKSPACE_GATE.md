# Workspace Gate — G513QM Hybrid Graphics Rebuild

## Confirmation

```text
============================================================
WORKSPACE BESTÄTIGUNG
============================================================
Aktueller Workspace: /tmp/piinstaller-install-assistant-001
Ziel-Workspace: /tmp/piinstaller-install-assistant-001
Git-Root: /tmp/piinstaller-install-assistant-001
Repository: https://github.com/Yammato-2035/piinstaller.git
Branch: pi-rs-install-assistant-001
HEAD: 9325415c28885e65613edb5f48f49719a35ceed6
origin/main: b8651d3337bf30b4443a622fdf8a6c9dc2995df5
Remote: origin → Yammato-2035/piinstaller.git
Dirty-Tree: yes (install-assistant G513QM work only; main checkout /home/volker/piinstaller NOT used)
Erwarteter Entwicklungsstrang: pi-rs-install-assistant-001
Arbeitsfreigabe: yes (STRICT MODE hybrid-graphics rebuild)
```

## Worktree selection

Compared ASUS-related worktrees; selected `/tmp/piinstaller-install-assistant-001` because it already contains Gabriel Mint/casper GRUB, rog-pack, and failure matrix. Other ASUS worktrees marked prunable and not mixed.

## Runtime gate

```text
./scripts/check-backend-version-gate.sh → exit 14
Drift: workspace project_version=1.9.20.3 vs api=1.9.21.2
```

Consequence: no Port-8000 smokes / telemetry acceptance claims. Static analysis, unit tests, stick file updates allowed.

## Stick identity (read-only snapshot)

| Field | Value |
|-------|-------|
| TRAN | usb |
| SIZE | 59G |
| MODEL | Ultra Line |
| VENDOR | Intenso |
| SERIAL | 24111412110686 |
| Kernel name (volatile) | /dev/sdc (do not use alone) |
| SETUPHELFER | UUID 9BB9-A4A6 |
| SETUP_LOGS | UUID 9BC7-3950 |
| Pack path | SETUP_LOGS/setuphelfer/rog-pack/g513qm/ |
