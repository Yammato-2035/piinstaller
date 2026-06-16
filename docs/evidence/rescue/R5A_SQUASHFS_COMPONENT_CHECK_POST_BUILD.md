# R.5A — SquashFS Komponenten-Check (Post-Build)

**ISO SHA256:** `4f511322e0d40e099f318dd959e6758c3404a0bbe80ace4d83a47dc67a77359e`  
**Methode:** read-only `xorriso` + `unsquashfs -ll` / `-cat`

## Tabelle

| Komponente | Status | Pfad / Hinweis | Risiko |
|------------|--------|----------------|--------|
| chromium | **MISSING** | `usr/bin/chromium` | critical |
| x-www-browser | **MISSING** | `usr/bin/x-www-browser` | critical |
| xserver-xorg | **MISSING** | `usr/bin/Xorg` | critical |
| xinit | **MISSING** | `usr/bin/xinit` | high |
| openbox | **MISSING** | `usr/bin/openbox` | critical |
| dbus-x11 | **MISSING** | `usr/bin/dbus-launch` | medium |
| x11-xserver-utils | **MISSING** | `usr/bin/xrandr` | low |
| unclutter | **MISSING** | `usr/bin/unclutter` | low |
| fonts-dejavu | **FOUND** | `usr/share/fonts/truetype/dejavu` | low |
| fonts-noto | **MISSING** | `usr/share/fonts/truetype/noto` | low |
| setuphelfer-rescue-kiosk-start | **FOUND** | `usr/local/sbin/…` | — |
| setuphelfer-rescue-kiosk-health | **FOUND** | `usr/local/sbin/…` | — |
| setuphelfer-rescue-evidence.py | **FOUND** | `usr/local/sbin/…` | — |
| setuphelfer-rescue-telemetry-push | **FOUND** | `usr/local/sbin/…` | — |
| Openbox autostart | **FOUND** | `etc/xdg/openbox/autostart` | — (openbox binary fehlt) |
| rescue.html | **FOUND** | `usr/share/setuphelfer/rescue/ui/rescue.html` | — |
| rescue JS bundle | **FOUND** | `assets/rescue-BE5PiphK.js` | — |
| /opt/setuphelfer-rescue | **FOUND** | `MANIFEST.json`, 2819 files | — |
| R.3 rescue_persistence.py | **MISSING** | nicht in opt-Bundle | critical |
| R.3 rescue_test_matrix.py | **MISSING** | nicht in opt-Bundle | critical |
| R.3 rescue_boot_logger.py | **MISSING** | nicht in opt-Bundle | high |
| R.3 rescue_evidence_bundle.py | **MISSING** | nicht in opt-Bundle | critical |
| R.3 rescue_telemetry_spool.py | **MISSING** | nicht in opt-Bundle | high |
| R.4 Matrix Version 4 | **MISSING** | kein Modul im Image | critical |
| setuphelfer-evidence Verzeichnisstruktur | **RUNTIME** | wird beim Boot angelegt, nicht im ISO-Root | — |

## Root Cause

1. **Package-Liste Drift:** `setuphelfer.list.chroot` im Build-Tree = 37 Zeilen (ohne R.4-Pakete); Git-Commit = 48 Zeilen.
2. **Bundle Drift:** `source_head=a8de59e` statt `57e30d9` — temp-runtime-Bundle ohne R.3-Module.

## filesystem.packages

`chromium`, `openbox`, `xserver-xorg` **nicht** in `/live/filesystem.packages`.

## Status

**`blocked_missing_runtime_components`**
