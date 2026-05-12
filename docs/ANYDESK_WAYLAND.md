# AnyDesk stürzt beim Start ab (Wayland)

Unter **Wayland** kann AnyDesk beim Start abstürzen oder sich sofort beenden. Das ist eine bekannte Einschränkung von AnyDesk.

## Ursache

- **Eingehende Verbindungen** (jemand verbindet sich zu deinem Pi) werden von AnyDesk unter Linux **nur unter Xorg** unterstützt.
- Unter einer **Wayland-Session** ist der Dienst/Die Anwendung oft nicht stabil – AnyDesk stürzt beim Start ab oder funktioniert nicht zuverlässig.

## Optionen

### 1. AnyDesk-Autostart deaktivieren (empfohlen bei Wayland)

Wenn du Wayland nutzt und AnyDesk nur gelegentlich brauchst:

- **Autostart ausschalten:** AnyDesk nicht beim Anmelden starten lassen (Einstellungen von AnyDesk oder Autostart-Ordner/`.config/autostart` prüfen und AnyDesk-Eintrag entfernen oder deaktivieren).
- AnyDesk **manuell starten**, wenn du es brauchst (z. B. nur für ausgehende Verbindungen). Unter Wayland können **ausgehende** Verbindungen oft genutzt werden, **eingehende** sind das Problem.

### 2. Session auf Xorg umstellen

Wenn du **eingehende** AnyDesk-Verbindungen zum Pi brauchst:

- Beim **Anmelden** die **Xorg-Session** wählen (z. B. „Pix (X11)“ oder „LXDE-pi“ statt „Pix (Wayland)“ / „Wayfire“), sofern verfügbar.
- Oder in den **Anmeldemanager-Einstellungen** Xorg als Standard-Session setzen.

Dann läuft der Desktop unter X11 und AnyDesk kann eingehende Verbindungen anzeigen. Nachteil: Du nutzt nicht mehr Wayland (z. B. für bessere DSI/HDMI-Konfiguration).

### 3. AnyDesk nur bei Bedarf starten

- AnyDesk **nicht** in den Autostart legen.
- Bei Bedarf aus dem Menü oder per Terminal starten: `anydesk`
- So vermeidest du den Crash beim Session-Start; unter Wayland bleiben eingehende Verbindungen weiterhin eingeschränkt.

## Kurzfassung

| Ziel | Maßnahme |
|------|----------|
| Kein Crash beim Start (Wayland behalten) | AnyDesk-Autostart deaktivieren, AnyDesk nur manuell starten |
| Eingehende AnyDesk-Verbindungen nutzen | Beim Login Xorg-Session wählen (nicht Wayland) |

Quellen: [AnyDesk Linux/Raspberry Pi](https://support.anydesk.com/anydesk-for-linux-raspberry-pi), [Flathub AnyDesk Issue #72](https://github.com/flathub/com.anydesk.Anydesk/issues/72).

---

## Zwei AnyDesk-Icons / Flackern (X11)

Unter X11 können **zwei AnyDesk-Icons** in der Taskleiste erscheinen oder flackern – meist weil zwei AnyDesk-Instanzen laufen (z. B. Autostart und manueller Start).

**Prüfen, ob AnyDesk doppelt gestartet wird:**

- `./scripts/fix-anydesk-double-icon.sh --check` – zeigt die Anzahl laufender AnyDesk-Prozesse, Autostart-Einträge (`~/.config/autostart`, `/etc/xdg/autostart`) und ggf. Systemd-User-Services. Mehr als ein Prozess oder mehrere Autostart-Dateien können zwei Icons / Flackern verursachen.

**Lösung:**

1. **Eine Instanz beenden:** `./scripts/fix-anydesk-double-icon.sh` – beendet alle AnyDesk-Prozesse und startet genau eine Instanz neu. Danach sollte nur noch ein Icon sichtbar sein.
2. **Falls das Flackern bleibt:** AnyDesk deinstallieren: `sudo ./scripts/fix-anydesk-double-icon.sh --uninstall`

**Hinweis:** Die Meldung `(anydesk): Gdk-CRITICAL **: gdk_window_thaw_toplevel_updates: assertion 'window->update_and_descendants_freeze_count > 0' failed` ist eine bekannte AnyDesk/GTK-Warnung (Ungleichgewicht zwischen Freeze/Thaw-Aufrufen). Sie erscheint oft beim Start oder Neustart von AnyDesk und ist in der Regel **harmlos** – AnyDesk funktioniert weiter. Sie kann ignoriert werden; ein Fix liegt bei AnyDesk/GTK.
