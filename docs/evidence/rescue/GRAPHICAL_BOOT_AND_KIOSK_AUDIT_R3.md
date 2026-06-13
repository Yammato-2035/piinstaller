# R.3 — Grafisches GRUB / Browser / Kiosk Audit

**Methode:** Repo-Analyse (kein apt install, kein Live-Boot in dieser Phase)

## Matrix

| Feature | vorhanden | aktiviert | getestet | Blocker | Nächste Aktion |
|---------|-----------|-----------|----------|---------|----------------|
| GRUB Theme Assets | ja | teilweise | nein | Theme muss im ISO landen | `stage-rescue-graphical-assets.sh` in Build-Pipeline verifizieren |
| GRUB theme.txt | ja (Staging) | unbekannt | nein | live-build `auto/config` ohne expliziten theme-Hook | grub.cfg/theme-Referenz im Binary-Image prüfen |
| ISOLINUX Fallback | unklar | — | nein | Kein Treffer in live-build auto/ | BIOS-Pfad separat auditieren (R.4) |
| Splash/Logo PNGs | ja (`assets/rescue/`) | ja (Staging) | nein | — | Nach nächstem ISO-Build visuell prüfen |
| React Rescue UI Bundle | ja (wenn `build/rescue/ui` gebaut) | ja | nein | Bundle muss im Image sein | Controlled ISO Build |
| HTTP-Server (UI) | ja (`setuphelfer-rescue-ui-launch`) | ja | nein | — | QEMU/MSI-Boot |
| Browser (chromium/firefox) | **nein** in package-list | nein | nein | **Paket fehlt** | `setuphelfer.list.chroot` ergänzen (Build, nicht apt) |
| X11/Wayland | **nein** (nur `x11-xkb-utils`) | nein | nein | Kein Display-Server | `xorg`/`openbox` oder `lxqt` in package-list vorbereiten |
| Kiosk-Autostart | nein | nein | nein | Browser+Display fehlen | systemd user service nach Browser-Build |
| TUI-Fallback | ja | ja | ja (statisch) | — | Standard bis Grafik-Stack im Image |

## Package-Liste (`setuphelfer.list.chroot`)

Enthält: Network-Stack, `whiptail`, Firmware, Python — **kein** `chromium`, `firefox`, `openbox`, `lxqt`, `xorg`.

## UI-Launcher (`setuphelfer-rescue-ui-launch`)

Sucht `chromium`, `chromium-browser`, `firefox-esr`, `firefox` — bei Fehlen: ehrlicher Status `browser_missing`, Fallback TUI.

## GRUB Staging (`stage-rescue-graphical-assets.sh`)

- Kopiert PNGs nach `includes.chroot` und `includes.binary/boot/grub/themes/setuphelfer/`
- Erzeugt `theme.txt` mit `desktop-image`
- Manifest: `build/rescue/asset-manifest.json`

## Empfehlung R.4

1. Browser + minimaler Display-Stack in `setuphelfer.list.chroot` (nur Build-Konfiguration)
2. Kiosk-Autostart-Skript + systemd user unit
3. GRUB-Theme-Aktivierung in fertigem `grub.cfg` verifizieren
4. MSI-Boot mit Matrix-Einträgen R3-GRAPH-*, R3-BROWSER-*
