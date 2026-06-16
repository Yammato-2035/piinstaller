# R.5A Remediation — Prepare Tree After Sync

**Datum:** 2026-06-13  
**Skript:** `./scripts/rescue-live/prepare-controlled-live-build-tree.sh`  
**Build-Root:** `build/rescue/live-build/setuphelfer-rescue-live`

## Ausführung

```
OK: Rescue React UI built -> build/rescue/ui
OK: graphical assets staged
OK: controlled live build tree at .../setuphelfer-rescue-live
OK: rescue_build_profile=standard
OK: bundle copied to includes.chroot/opt/setuphelfer-rescue (2938 files ref)
```

Kein `lb build`, kein ISO.

## Package-List

| Check | Ergebnis |
|-------|----------|
| Zeilen | **48** |
| R.4 Browser/Display | **alle vorhanden** |

## R.4 Staging (includes.chroot)

| Artefakt | Status |
|----------|--------|
| `usr/local/sbin/setuphelfer-rescue-kiosk-start` | staged, 0755 |
| `usr/local/sbin/setuphelfer-rescue-kiosk-health` | staged, 0755 |
| `usr/local/sbin/setuphelfer-rescue-evidence.py` | staged, 0755 |
| `usr/local/sbin/setuphelfer-rescue-telemetry-push` | staged, 0755 |
| `etc/xdg/openbox/autostart` | staged |
| `usr/share/setuphelfer/rescue/ui/rescue.html` | staged |

## R.3 Core-Module (`includes.chroot/opt/setuphelfer-rescue/backend/core/`)

| Modul | Status |
|-------|--------|
| `rescue_persistence.py` | vorhanden |
| `rescue_test_matrix.py` | vorhanden |
| `rescue_telemetry_spool.py` | vorhanden |
| `rescue_evidence_bundle.py` | vorhanden |

## Build-Tree-Manifest

`evidence/build-tree-manifest.json` → `source_head=57e30d9`, `bundle_files_count=2938`

## Stale Chroot

Root-owned `chroot/` vom vorherigen Operator-ISO-Build nach `build/rescue/.chroot-stale-r5a-remediation-*` verschoben (kein sudo). Vor Rebuild empfiehlt Operator zusätzlich `sudo ./auto/clean` im Build-Root.
