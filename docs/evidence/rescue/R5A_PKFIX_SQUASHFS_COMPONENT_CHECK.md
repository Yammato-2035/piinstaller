# R.5A PKFix — SquashFS Component Check

**ISO:** `binary.hybrid.iso`  
**SHA256:** `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143`  
**Methode:** read-only `xorriso` extract + `unsquashfs -ll/-cat`  
**Validator:** `validate-rescue-iso-squashfs.sh` → **Exit 0**

## Tabelle

| Komponente | Status | Pfad (SquashFS) | Pflicht | Ampel |
|------------|--------|-----------------|---------|-------|
| chromium | **FOUND** | `usr/bin/chromium` | ja | green |
| xserver-xorg | **FOUND** | `usr/bin/Xorg`, `xserver-xorg-*` pkgs | ja | green |
| xinit | **FOUND** | `usr/bin/xinit` | ja | green |
| openbox | **FOUND** | `usr/bin/openbox` | ja | green |
| dbus-x11 | **FOUND** | `usr/bin/dbus-launch` | ja | green |
| x11-xserver-utils | **FOUND** | `usr/bin/xset`, `usr/bin/xrandr` | ja | green |
| unclutter | **FOUND** | `usr/bin/unclutter` → `unclutter-classic` | ja | green |
| fonts-dejavu | **FOUND** | `usr/share/fonts/truetype/dejavu/` | ja | green |
| fonts-noto | **FOUND** | `usr/share/fonts/truetype/noto/` | ja | green |
| x-www-browser (runtime alt) | **FOUND** | `etc/alternatives/x-www-browser` → chromium | nein | green |
| kiosk-start | **FOUND** | `usr/local/sbin/setuphelfer-rescue-kiosk-start` | ja | green |
| kiosk-health | **FOUND** | `usr/local/sbin/setuphelfer-rescue-kiosk-health` | ja | green |
| Openbox autostart | **FOUND** | `etc/xdg/openbox/autostart` | ja | green |
| evidence.py | **FOUND** | `usr/local/sbin/setuphelfer-rescue-evidence.py` | ja | green |
| telemetry-push | **FOUND** | `usr/local/sbin/setuphelfer-rescue-telemetry-push` | ja | green |
| rescue.html | **FOUND** | `usr/share/setuphelfer/rescue/ui/rescue.html` | ja | green |
| rescue JS bundle | **FOUND** | `usr/share/setuphelfer/rescue/ui/assets/rescue-BE5PiphK.js` | ja | green |
| rescue_persistence.py | **FOUND** | `opt/setuphelfer-rescue/backend/core/rescue_persistence.py` | ja | green |
| rescue_test_matrix.py | **FOUND** | `opt/setuphelfer-rescue/backend/core/rescue_test_matrix.py` | ja | green |
| rescue_telemetry_spool.py | **FOUND** | `opt/setuphelfer-rescue/backend/core/rescue_telemetry_spool.py` | ja | green |
| rescue_evidence_bundle.py | **FOUND** | `opt/setuphelfer-rescue/backend/core/rescue_evidence_bundle.py` | ja | green |
| MANIFEST source_head | **FOUND** | `57e30d9` (2938 files) | ja | green |
| Matrix Version 4 | **FOUND** | `RESCUE_TEST_MATRIX_VERSION = 4` | ja | green |

## Gesamt

**Alle Pflichtkomponenten FOUND** — kein `blocked_missing_runtime_components` aus SquashFS-Sicht.
