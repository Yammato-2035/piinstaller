# DSI-Spiegelung auf HDMI unter X11 (Raspberry Pi)

**Stand (1.3.3.0):** Dual Display X11 (DSI + HDMI) läuft stabil: Position (DSI links unten, HDMI rechts oben), Desktop/Hintergrund auf HDMI (Primary), kein ständiges Umschalten. Layout und Desktop-Zuordnung werden über .xprofile (~10 s) und delayed-Script (8 s / 16 s) gesetzt.

## Problem

Der **komplette Desktop des DSI-1** wird oben links auf dem HDMI-1-2 angezeigt (gespiegelt). Es geht nicht um ein einzelnes Fenster, sondern um die gesamte DSI-Anzeige, die im linken oberen Bereich des HDMI-Bildschirms erscheint.

Ursache ist typischerweise das Verhalten des Pi-KMS/DRM-Treibers: Der Framebuffer oder die Scanout-Region für HDMI wird nicht korrekt ab Offset (480,0) gelegt, sodass der linke Bereich des HDMI-Ausgangs den Inhalt anzeigt, der eigentlich für DSI bestimmt ist.

## Umgesetzte Maßnahmen in den Scripts

1. **Explizite Framebuffer-Größe**  
   `xrandr --fb 3920x2240` (480+3440 × 1440+800) wird gesetzt. Das zwingt einen klaren virtuellen Screen und kann die falsche Zuordnung verhindern.

2. **Beide Ausgaben in einem atomaren xrandr-Befehl**  
   `--fb` und beide `--output … --pos …` werden in **einem** xrandr-Aufruf gesetzt (analog zu Wayland/Kanshi, wo pro Output-Name eine Position gesetzt wird). So soll die Position pro Output-Name zugeordnet werden: DSI-1 bei (0,1440), HDMI-1-2 bei (480,0). Unter Wayland hatte dasselbe Layout funktioniert; unter X11 kann die getrennte Anwendung pro Befehl dazu führen, dass der Treiber nach Connector-Reihenfolge statt nach Namen zuordnet.

3. **Pi 5 Connector-Zuordnung**  
   DSI-1 hängt an Anschluss 0 (äquivalent zu HDMI-1-1); der Hauptmonitor ist an HDMI-1-2. Die virtuelle Anordnung „DSI links unten, HDMI rechts oben“ ist eine Einstellung und unter Wayland erreichbar; unter X11 wird sie durch den atomaren Befehl angestrebt.

3. **Verwendung in allen relevanten Scripts**  
   - `fix-gabriel-dual-display-x11.sh` (xrandr, .xprofile, .screenlayout)  
   - `apply-dual-display-x11-delayed.sh`  
   - `fix-dsi-position-x11.sh`  
   - `fix-hdmi-dark-screen-x11.sh` setzt HDMI bereits auf 480x0

## Nach Reboot: DSI wieder rechts oben

Wenn die Positionierung vor dem Reboot stimmte, nach dem Reboot aber DSI wieder rechts oben ist, überschreibt vermutlich die DE oder ein Monitor-Daemon die Anordnung. Dagegen:

- **.xprofile** wartet jetzt **8 s** (statt 3 s), damit HDMI beim ersten xrandr-Aufruf bereit ist.
- **apply-dual-display-x11-delayed.sh** wendet das Layout nach **8 s** und **16 s** an. **.xprofile** startet ~10 s nach Login PCManFM-Desktop neu (Trigger für Desktop → HDMI).

Falls DSI nach dem Reboot trotzdem rechts oben bleibt: Manuell `./scripts/fix-dsi-position-x11.sh` ausführen oder ca. 20 s nach Login warten.

## Desktop/Hintergrund auf DSI statt auf HDMI (LXDE/PCManFM)

**Symptom:** Die Position stimmt (DSI links unten, HDMI rechts oben), die Taskleiste ist auf HDMI-1-2, aber **Desktop-Icons, Hintergrund und „Desktop-Ordner“** erscheinen auf DSI-1. Im Control Center ist HDMI-1-2 mit Coast-Hintergrund eingestellt; trotzdem zeigt DSI den Hauptdesktop.

**Ursache:** LXDE/PCManFM nutzt oft den **linkesten** Monitor (x=0) für den Hauptdesktop, nicht den xrandr-**Primary**. Bei unserem Layout liegt DSI bei x=0 (links unten), HDMI bei x=480 (rechts oben). Daher wird der Desktop auf DSI angezeigt.

**Maßnahmen:**

1. **apply-dual-display-x11-delayed.sh** startet nach dem zweiten Layout-Apply (~28 s) **PCManFM-Desktop neu** (`killall pcmanfm`; dann `pcmanfm --desktop --profile …`). So soll die Anzeige nach Primary (HDMI) neu ausgerichtet werden. Ca. 30 s nach Login prüfen, ob Desktop und Hintergrund nun auf HDMI erscheinen.

2. **Manuell:** `./scripts/fix-desktop-on-hdmi-x11.sh` (siehe unten) – PCManFM-Desktop neu starten, um den Versuch zu wiederholen.

3. **Falls es nicht hilft:** Bekannte Einschränkung von LXDE/PCManFM (Desktop folgt dem linkesten Bildschirm). Ohne Layout-Änderung (HDMI auf x=0 setzen, was die Maus-Logik umdrehen würde) gibt es unter X11 oft keine zuverlässige Lösung. Alternative: Kontrolle über Control Center → Anzeige (Primary setzen) und ggf. Ab- und erneutes Anmelden.

## Wenn DSI trotzdem rechts oben erscheint

Unter Wayland (Kanshi/wlr-randr) wird die Position pro Output-Name gesetzt und das Layout „DSI links unten, HDMI rechts oben“ funktioniert. Unter X11 wird nun **ein atomarer xrandr-Befehl** mit beiden Ausgaben verwendet, damit die Zuordnung ebenfalls nach Output-Name erfolgt. Wenn DSI-1 danach weiterhin physisch rechts oben erscheint, kann der vc4-KMS-Treiber die Position dennoch nach Connector-Reihenfolge vergeben. Dann bleiben als Optionen: config.txt (z. B. Connector-/Firmware-Reihenfolge), Treiber-Update oder manueller Test mit `xrandr --crtc` (CRTC explizit pro Ausgabe setzen).

## Wenn die Spiegelung bleibt: Optionen

### config.txt (Boot-Partition)

Unter `/boot/firmware/config.txt` (oder `/boot/config.txt`) können zusätzliche Optionen getestet werden. **Nur anpassen, wenn die Spiegelung trotz --fb und Reihenfolge bestehen bleibt.**

- **max_framebuffers=2**  
  Sollte für DSI+HDMI bereits gesetzt sein (z. B. durch `setup-pi5-dual-display-dsi-hdmi0.sh`).

- **framebuffer_priority** (falls vom Pi unterstützt)  
  Beeinflusst, welcher Ausgang als „erstes“ Framebuffer-Objekt behandelt wird. Wenn DSI als erstes Objekt den linken Bereich belegt, kann ein Wechsel der Priorität (z. B. HDMI zuerst) helfen. Dokumentation des jeweiligen Pi-Modells prüfen (z. B. Raspberry Pi Forums, offizielle config.txt-Doku).

- **Neustart**  
  Änderungen in config.txt sind erst nach Reboot aktiv.

### Treiber / System-Updates

- System und Firmware aktuell halten (`sudo apt update && sudo apt full-upgrade`).
- Bekannte Fixes für DSI+HDMI unter KMS in den Release Notes und Raspberry Pi Forums prüfen.

### Manueller Test

Nach Login in der Konsole (ohne Desktop):

```bash
xrandr --fb 3920x2240
xrandr --output HDMI-1-2 --auto --primary --pos 480x0
xrandr --output DSI-1 --mode 800x480 --rotate left --pos 0x1440
```

Wenn die Spiegelung danach weg ist, ist die Konfiguration in den Scripts ausreichend; sie wird dann auch über .xprofile und das verzögerte Autostart-Script angewendet.

## Relevante Dateien

| Datei | Zweck |
|-------|------|
| `scripts/fix-gabriel-dual-display-x11.sh` | Haupt-Setup, .xprofile, .screenlayout |
| `scripts/apply-dual-display-x11-delayed.sh` | Verzögerte Anwendung nach Login |
| `scripts/fix-dsi-position-x11.sh` | Schneller manueller Fix (Position + --fb) |
| `scripts/fix-hdmi-dark-screen-x11.sh` | HDMI wieder aktivieren, Position 480x0 |
| `~/.xprofile` | Wird beim X11-Login ausgeführt (sleep 8, dann atomarer xrandr) |
| `apply-dual-display-x11-delayed.sh` | Autostart ~8 s und ~16 s nach Login (Layout + ggf. PCManFM-Neustart) |

## Layout (zur Erinnerung)

- **DSI-1:** links unten, Portrait 480×800, Position (0, 1440)  
- **HDMI-1-2:** rechts daneben, oben, Position (480, 0)  
- Virtueller Screen: 3920×2240 Pixel

## Siehe auch

- **FAQ in der App:** Dokumentation → FAQ – „DSI-Desktop oben links auf HDMI gespiegelt (X11)“ und „Dual Display X11 (DSI + HDMI) – Desktop auf HDMI, stabil“
- **Changelog:** [CHANGELOG.md](../CHANGELOG.md) – Version 1.3.3.0 (stabil ohne Umschalten), 1.3.2.0 (Spiegelung)
