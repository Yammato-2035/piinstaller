# R.4 — Package-List Änderung

**Datei geändert:** `setuphelfer.list.chroot`  
**Methode:** Build-Konfiguration (kein `apt install` auf Host)

## Hinzugefügte Pakete

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

## Browser-Entscheidung

- **Primär:** `chromium` + `x-www-browser` (Alternatives-Ziel)
- **Fallback-Dokumentation:** `firefox-esr` falls Chromium im Live-Build zu groß oder nicht verfügbar — **nicht** parallel erzwungen
- Begründung: `setuphelfer-rescue-ui-launch` und `setuphelfer-rescue-kiosk-start` suchen zuerst chromium-Varianten

## Display-Entscheidung

- **Minimal:** `xserver-xorg` + `xinit` + `openbox`
- Kein lightdm/weston in R.4 (Kiosk über openbox autostart)

## Kiosk-Autostart (Build)

`config/includes.chroot/etc/xdg/openbox/autostart` → ruft `setuphelfer-rescue-kiosk-start` auf

## Nächster Schritt

Controlled ISO Build in **R.5** — dann SquashFS-Listing auf chromium/openbox prüfen.
