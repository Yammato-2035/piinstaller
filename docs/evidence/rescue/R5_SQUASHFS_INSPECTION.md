# R.5 — SquashFS-Inspektion

## ISO

`build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso`  
SHA256: `c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194`  
**Hinweis:** ISO vom **2026-06-07**, **vor R.4** — read-only Inspektion zeigt erwarteten Drift.

## Kiosk-/R.4-Stack (unsquashfs -ll)

| Pfad | Status |
|------|--------|
| usr/bin/chromium | **MISSING** |
| usr/bin/x-www-browser | **MISSING** |
| usr/bin/Xorg | **MISSING** |
| usr/bin/openbox | **MISSING** |
| usr/local/sbin/setuphelfer-rescue-kiosk-start | **MISSING** |
| usr/local/sbin/setuphelfer-rescue-kiosk-health | **MISSING** |
| usr/local/sbin/setuphelfer-rescue-evidence.py | **MISSING** |
| usr/local/sbin/setuphelfer-rescue-telemetry-push | **MISSING** |
| etc/xdg/openbox/autostart | **MISSING** |
| usr/share/setuphelfer/rescue/ui/rescue.html | **MISSING** |

## Legacy-Validierung

`validate-rescue-iso-squashfs.sh` → **Exit 0** (ältere Bundle/systemd-Kriterien erfüllt).

## Bewertung

**`blocked_squashfs_missing_kiosk_stack`** für R.5-Abnahme.

→ **Kein USB-Write** mit dieser ISO. Neuer Build mit Gate A erforderlich.

## Nach neuem Build prüfen

Gleiche Tabelle erneut ausführen; alle R.4-Pfade müssen **FOUND** sein.
