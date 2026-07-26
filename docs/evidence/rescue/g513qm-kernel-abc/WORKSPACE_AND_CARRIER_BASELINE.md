# Workspace and carrier baseline — G513QM Kernel A/B/C

```text
============================================================
WORKSPACE BESTÄTIGT
============================================================
Workspace: /tmp/piinstaller-install-assistant-001
Git-Root: /tmp/piinstaller-install-assistant-001
Repository: https://github.com/Yammato-2035/piinstaller.git
Branch: pi-rs-install-assistant-001
HEAD: 4e171c6b0ecc4ab5ee5e7af4fe085d9aa727fcf7
origin/main: b8651d3337bf30b4443a622fdf8a6c9dc2995df5
Remote: origin → Yammato-2035/piinstaller.git
Dirty-Tree: clean at gate start
Runtime-Gate: check-backend-version-gate.sh exit 14 (workspace 1.9.20.3 vs api 1.9.21.2)
Arbeitsmodus: static_and_build_only
```

## Carrier (Intenso stick)

| Field | Value |
|-------|-------|
| TRAN | usb |
| SIZE | 59G |
| MODEL | Ultra Line |
| SERIAL | 24111412110686 |
| SETUPHELFER UUID | 9BB9-A4A6 |
| SETUP_LOGS UUID | 9BC7-3950 |
| Volatile name | /dev/sdb (do not use alone) |

## Baseline snapshot

Directory: `baseline-20260726T130033Z/`

- `grub.cfg` (SHA256 in `SHA256SUMS`) — default **Basic Emergency (nomodeset)**
- Pack `MANIFEST.json` + graphics profiles copy when present

## Safety

Internal NVMe (`nvme0n1` Windows, `nvme1n1` host Linux) are **out of scope** for writes in this phase.
