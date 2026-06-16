# R.5A Rebuild Unblock — Clean Dry-Run

**Datum:** 2026-06-13T18:14:16+02:00  
**Befehl:**

```bash
cd /home/volker/piinstaller
./scripts/rescue-live/clean-controlled-live-build-tree.sh --dry-run
```

**Exit:** 0

## Vollständiger Output

```
=== clean-controlled-live-build-tree 2026-06-13T18:14:16+02:00 ===
REPO_ROOT=/home/volker/piinstaller
BUILD_ROOT=/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live
CONFIRM=false DRY_RUN=true
EUID=1002 USER=gabriel
TARGET: .../binary
TARGET: .../binary.contents
TARGET: .../binary.packages
TARGET: .../cache
TARGET: .../chroot.headers
TARGET: .../chroot.packages.install
TARGET: .../chroot.packages.live
TARGET: .../wget-log
TARGET: .../wget-log.1
TARGET: .../wget-log.2
TARGET: .../wget-log.3
WARN: 11 target(s) are root-owned. Re-run with sudo for removal.
DRY-RUN: would remove 11 path(s). Pass --operator-confirm-clean to apply.
```

## Bewertung: Dry-Run plausibel

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Nur Build-Tree-Artefakte | **ja** — alle TARGETs unter `build/rescue/live-build/setuphelfer-rescue-live/` |
| Keine Repo-Quellen | **ja** — kein `backend/`, `scripts/`, `frontend/` |
| Keine docs/evidence | **ja** |
| Keine config-Quellen | **ja** — `config/` im Build-Tree nicht gelistet |
| Keine USB/Device-Aktion | **ja** — nur `rm`-Ziele aus Policy `list_clean_targets` |

**Dry-run plausibel: ja** — Phase 2 (Operator-Clean) freigegeben.
