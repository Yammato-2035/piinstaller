# R.4 — Package-List Audit

**Datei:** `build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot`

## Vor R.4 (Ist)

| Kategorie | Paket | Vorhanden |
|-----------|-------|-----------|
| Browser | chromium | **nein** |
| Browser | firefox-esr | **nein** |
| Browser | x-www-browser | **nein** |
| Display | xserver-xorg | **nein** |
| Display | xinit | **nein** |
| Display | openbox | **nein** |
| Display | lightdm | nein |
| Display | weston/cage | nein |
| Hilfe | dbus-x11 | **nein** |
| Hilfe | x11-xserver-utils | **nein** |
| Hilfe | unclutter | **nein** |
| Fonts | fonts-dejavu | **nein** |
| Fonts | fonts-noto | **nein** |
| Netzwerk | network-manager | **ja** |
| Netzwerk | wpasupplicant | **ja** |
| Netzwerk | iw | **ja** |
| Netzwerk | wireless-tools | **nein** |
| TUI | whiptail | **ja** |
| Basis | x11-xkb-utils | **ja** (nur Tastatur, kein Display-Server) |

## Bewertung vor Änderung

- **Browser/Kiosk:** nicht bootfähig — `setuphelfer-rescue-ui-launch` fällt auf TUI zurück
- **Display-Stack:** fehlt vollständig
- **WLAN:** ausreichend für TUI-Netzwerk-Menü

## Nach R.4 (Soll — Build-Konfiguration)

Siehe `R4_PACKAGE_LIST_CHANGE.md`.

## Weitere package-lists

Kein separates `config/package-lists/` im Repo-Root — kanonische Liste nur im live-build tree.
