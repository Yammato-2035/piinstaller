# ASUS-02 Boot 17:31 UTC — gesammelte Daten + GUI-Fail

Payload: `55a144ae…` (tty1-Owner-Fix) · Profil: **ASUS-02** · Gerät: G513QM

## Was funktioniert hat

| Bereich | Status |
|---|---|
| Profil/Default | ASUS-02 korrekt |
| systemd failed units | **0** (kein SIGHUP-Storm mehr) |
| UI-Service | disabled / inactive (gewollt) |
| Start-Assistent | lief (`activating`, TUI+Watchdog im CGroup) |
| DRM/Panel | `amdgpudrmfb`, **eDP-1 connected** |
| Diagnose auf Stick | ja, `persistent_to_stick=true` |
| SquashFS-Hash | stimmte mit Payload überein |

## GUI-Ursache (belegt)

`gui-watchdog.json` / `gui-start.log`:

- Fehlercode: **`openvt_console_2_not_released`**
- openvt-Meldung: `Konsole 2 konnte nicht freigegeben werden`
- Danach Chromium ohne X: `Missing X server or $DISPLAY`
- Kein `/var/log/Xorg.0.log`

Fallback markiert: `fallback_to_tui=true`, `tui_rerendered_after_gui_failure=true`.
Console-Owner: `tui` — Operator sah dennoch oft „keine UI“ (tty1 vorher blanked).

## Auf dem Stick vorhanden (Auszug)

- `diagnostics/latest/` — Meta, dmidecode, lspci, lsmod, DRM, Netz, Journal, dmesg, ps, run-state
- `evidence/boot/` — boot_state, gui-watchdog, gui-fallback, rescue-ui-status
- `logs/boot/` — gui-start.log, x11-launch.log, chromium-launch.log, rescue-ui-launch.log

## Nächster Fix-Hebel

openvt VT2 freigeben / Kiosk ohne blockierenden openvt-`-w` auf belegter Console,
oder startx direkt auf VT1/VT2 nach dealloc; Console-Ownership für GUI-Transition erlauben.
