# R.5A Remediation — Package-List Sync

**HEAD:** `57e30d9`

## Maßnahmen

1. `git checkout HEAD -- build/.../setuphelfer.list.chroot` → 48 Zeilen
2. `prepare-controlled-live-build-tree.sh` Heredoc um R.4-Pakete (Z. 38–48) ergänzt — dauerhafte Korrektur der Root Cause

## Vorher / Nachher

| | Zeilen | Endzeile |
|---|--------|----------|
| **vorher** | 37 | `whiptail` |
| **nachher** | 48 | `wireless-tools` |

## Akzeptanz-Grep (Exit 0)

```
xserver-xorg
xinit
openbox
chromium
dbus-x11
x11-xserver-utils
unclutter
fonts-dejavu
fonts-noto
x-www-browser
wireless-tools
```

## Keine Paket-Erfindung

Alle 11 R.4-Zeilen stammen 1:1 aus `git show 57e30d9:.../setuphelfer.list.chroot`. Kein `apt`, keine Umbenennung.

## Status

**package-list synchron** — ja
