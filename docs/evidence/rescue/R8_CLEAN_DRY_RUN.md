# R.8 — Clean Dry-Run

**Datum:** 2026-06-13

```bash
cd /home/volker/piinstaller
./scripts/rescue-live/clean-controlled-live-build-tree.sh --dry-run
```

## Output

```
=== clean-controlled-live-build-tree 2026-06-13T22:16:55+02:00 ===
REPO_ROOT=/home/volker/piinstaller
BUILD_ROOT=/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live
CONFIRM=false DRY_RUN=true
EUID=1002 USER=gabriel
TARGET: .../setuphelfer-rescue-live/.build
TARGET: .../setuphelfer-rescue-live/binary
TARGET: .../setuphelfer-rescue-live/binary.contents
TARGET: .../setuphelfer-rescue-live/binary.hybrid.iso
TARGET: .../setuphelfer-rescue-live/binary.packages
TARGET: .../setuphelfer-rescue-live/cache
TARGET: .../setuphelfer-rescue-live/chroot
TARGET: .../setuphelfer-rescue-live/chroot.headers
TARGET: .../setuphelfer-rescue-live/chroot.packages.install
TARGET: .../setuphelfer-rescue-live/chroot.packages.live
TARGET: .../setuphelfer-rescue-live/local
TARGET: .../setuphelfer-rescue-live/wget-log
TARGET: .../setuphelfer-rescue-live/wget-log.1
TARGET: .../setuphelfer-rescue-live/wget-log.2
TARGET: .../setuphelfer-rescue-live/wget-log.3
WARN: 13 target(s) are root-owned. Re-run with sudo for removal.
DRY-RUN: would remove 15 path(s). Pass --operator-confirm-clean to apply.
```

Exit: **0**

## Bewertung

| Kriterium | Ergebnis |
|-----------|----------|
| Nur `build/rescue/live-build/setuphelfer-rescue-live/*` | **ja** |
| `.build`, `binary`, `cache`, `chroot`, ISO-Artefakte | **ja** |
| Repo-Quellen (`backend/`, `scripts/`, `docs/`) | **nein** |
| `docs/evidence` | **nein** |
| `config/` außerhalb Build-Tree | **nein** |

**Dry-run plausibel — weiter mit Clean Execute.**
