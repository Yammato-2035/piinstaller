# R.5A PKFix — filesystem.packages Check

**Pfad:** `build/rescue/live-build/setuphelfer-rescue-live/binary/live/filesystem.packages`  
**Zeilen:** 708  
**Format:** `pkgname\tversion` (live-build Standard)

## Pflichtpakete

| Paket | Status | Version (Auszug) |
|-------|--------|------------------|
| chromium | **FOUND** | `149.0.7827.102-1~deb12u1` |
| openbox | **FOUND** | `3.6.1-10` |
| xserver-xorg | **FOUND** | `1:7.7+23` (+ core/video/input) |
| xinit | **FOUND** | `1.4.0-1` |
| dbus-x11 | **FOUND** | `1.14.10-1~deb12u1` |
| unclutter | **FOUND** | `8-25` |
| x11-xserver-utils | **FOUND** | `7.7+9+b1` |
| fonts-dejavu | **FOUND** | `2.37-6` |
| fonts-noto | **FOUND** | `20201225-1` (+ core/extra) |

## Explizit nicht vorhanden (korrekt)

| Paket | Status |
|-------|--------|
| **x-www-browser** | **ABSENT** — kein apt-Paket, nur Runtime-Alternative via chromium |

## Fazit

Package-Manifest bestätigt PKFix: Browser/Display-Stack installiert, invalides `x-www-browser`-Paket nicht gelistet.
