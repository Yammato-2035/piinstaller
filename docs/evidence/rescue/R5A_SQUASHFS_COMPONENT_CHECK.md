# R.5A — SquashFS Komponenten-Prüfung

## ISO

**Stale** (2026-06-07) — einzige vorhandene ISO bis Neubau.

SHA256: `c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194`

## Tabelle (read-only unsquashfs -ll)

| Komponente | Status |
|------------|--------|
| chromium (`usr/bin/chromium`) | **MISSING** |
| x-www-browser | **MISSING** |
| xserver-xorg (`usr/bin/Xorg`) | **MISSING** |
| openbox | **MISSING** |
| setuphelfer-rescue-kiosk-start | **MISSING** |
| setuphelfer-rescue-kiosk-health | **MISSING** |
| setuphelfer-rescue-evidence.py | **MISSING** |
| setuphelfer-rescue-telemetry-push | **MISSING** |
| Openbox-Autostart (`etc/xdg/openbox/autostart`) | **MISSING** |
| rescue.html | **MISSING** |
| setuphelfer-evidence Verzeichnisstruktur | **MISSING** (Runtime, nicht Build-Artefakt) |
| R.4 Testmatrix v4 im Image | **MISSING** (Backend-Module nicht im stale SquashFS) |

## Nach neuem Build erneut prüfen

```bash
ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
WORK=$(mktemp -d)
xorriso -osirrox on -indev "$ISO" -extract /live/filesystem.squashfs "$WORK/fs.squashfs"
# dann FOUND/MISSING für alle Pflichtkomponenten
```

## Bewertung

**`blocked_missing_runtime_components`** — alle Pflichtkomponenten MISSING in aktueller ISO.
