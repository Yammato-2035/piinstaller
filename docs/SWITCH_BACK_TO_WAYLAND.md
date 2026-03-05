# Zurück zu Wayland wechseln (Raspberry Pi OS Bookworm)

Wenn unter **Wayland** der Ton aus den Freenove-Gehäuselautsprechern kam und unter **X11** nicht (HDMI-A-1 bleibt disabled, Ton nur aus dem Monitor), ist der Wechsel zurück zu Wayland die sinnvollste Lösung.

## Vorgehen

### 1. raspi-config öffnen

```bash
sudo raspi-config
```

### 2. Wayland auswählen

- **Advanced Options** (Erweiterte Optionen) öffnen
- **A6 Wayland** auswählen
- **Wayland** (oder **labwc**) als Backend wählen und bestätigen
- Mit **Finish** beenden

### 3. Neustart

```bash
sudo reboot
```

### 4. Beim Anmelden Wayland-Session wählen

Nach dem Neustart beim **Login** die Session wählen:

- **„Pix (Wayland)“** oder **„Wayfire“** bzw. **„Labwc“** (je nach Angebot)
- **Nicht** „Pix (X11)“ oder „LXDE-pi (X11)“ wählen

### 5. Prüfen

```bash
echo $XDG_SESSION_TYPE
```

Sollte **wayland** ausgeben.

---

## Kurz

| Schritt | Aktion |
|--------|--------|
| 1 | `sudo raspi-config` |
| 2 | Advanced Options → A6 Wayland → Wayland (oder labwc) wählen |
| 3 | `sudo reboot` |
| 4 | Beim Login Wayland-Session wählen (nicht X11) |
| 5 | `echo $XDG_SESSION_TYPE` → sollte „wayland“ sein |

---

## Bezug Freenove-Audio

- Unter **Wayland** funktionieren HDMI-Hotplug und Audio-Routing für das Freenove Mediaboard zuverlässiger.
- Unter **X11** deaktivieren Skripte (z. B. `.xprofile`) oft HDMI-A-1, sodass kein Ton an den Gehäuselautsprechern ankommt.

Siehe auch: `docs/FREENOVE_AUDIO_TROUBLESHOOTING.md`, `docs/FREENOVE_AUDIO_DEEP_ANALYSIS.md`.
