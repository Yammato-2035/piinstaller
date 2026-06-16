# R.5A Remediation-2 — Package-List Fix

**Datum:** 2026-06-13

## Entfernt

```
x-www-browser
```

## Geänderte Quellen

| Quelle | Änderung |
|--------|----------|
| `scripts/rescue-live/prepare-controlled-live-build-tree.sh` | Heredoc: Zeile `x-www-browser` entfernt |
| `build/.../setuphelfer.list.chroot` | via Prepare neu geschrieben (47 Zeilen) |

`find . -path "*package-lists*" -name "setuphelfer.list.chroot"` → **eine** aktive Datei im Build-Tree.

## Unverändert (explizit beibehalten)

- chromium
- xserver-xorg, xinit, openbox
- dbus-x11, x11-xserver-utils, unclutter
- fonts-dejavu, fonts-noto
- wireless-tools, iw, wpasupplicant, network-manager

## Vorher / Nachher

| | Zeilen | x-www-browser |
|---|--------|---------------|
| vorher | 48 | ja (Z. 47) |
| nachher | **47** | **nein** |

## Zusätzlich

`validate-live-build-dpkg-preflight.sh`: `x-www-browser` in `FORBIDDEN_PACKAGES` aufgenommen.
