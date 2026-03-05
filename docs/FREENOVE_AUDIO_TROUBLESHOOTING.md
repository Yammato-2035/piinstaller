# Freenove Gehäuselautsprecher – Troubleshooting

**WICHTIG:** Siehe auch `docs/FREENOVE_AUDIO_DEEP_ANALYSIS.md` für eine umfassende Analyse der bekannten Raspberry Pi 5 HDMI-Audio-Regressionen und warum Audio früher funktionierte (Version 1.2.x.x).

## Freenove Audio von Null einrichten (Wayland)

Wenn du alles auf Standard zurücksetzen und ohne alte Fehleinstellungen (X11, falsche „Card 0“-Annahme, falsches Routing) neu einrichten willst:

**Voraussetzung:** Du nutzt **Wayland** (nicht X11). Die Karte für Gehäuselautsprecher wird über die **Plattform-ID 107c701400** (vc4hdmi0) erkannt, nicht über die ALSA-Kartennummer (Card 0 kann z. B. eine USB-Webcam sein).

**Schritt 1 – Zurücksetzen:**
```bash
./scripts/reset-freenove-audio-to-default.sh
```
Entfernt: WirePlumber-Konfiguration für HDMI-A-1 (system + user), Autostart „Freenove Standard-Sink“. Optional: WirePlumber-State löschen (dann wird der Standard-Sink neu gewählt).

**Schritt 2 – WirePlumber neu starten (als Benutzer, ohne sudo):**
```bash
systemctl --user restart wireplumber
sleep 4
```

**Schritt 3 – Konfiguration anlegen (nur für /etc wird sudo benötigt):**
```bash
sudo ./scripts/configure-wireplumber-hdmi-a1.sh
```
Danach **nochmals als Benutzer** WirePlumber neu starten:
```bash
systemctl --user restart wireplumber
sleep 4
```

**Schritt 4 – Sink aktivieren und als Standard setzen (als Benutzer):**
```bash
./scripts/activate-hdmi-a1-sink.sh
paplay /usr/share/sounds/alsa/Front_Left.wav
```

**Schritt 5 – Optional (HDMI-A-1 sehr früh + Standard-Sink nach Login):**
```bash
./scripts/install-freenove-default-sink-autostart.sh
```
Richtet einen systemd-User-Service ein, der **direkt nach WirePlumber** HDMI-A-1 aktiviert und als Standard setzt (sehr früh), plus Autostart als Fallback.

**Kurz:** Erst zurücksetzen, dann Konfiguration mit sudo schreiben, alle weiteren Schritte (WirePlumber-Neustart, Sink aktivieren, paplay) **ohne sudo** als dein Benutzer ausführen.

## Wenn unter Wayland Ton aus den Lautsprechern kam: Zurück zu Wayland wechseln

Unter **X11** bleibt HDMI-A-1 oft disabled und der Ton kommt nur aus dem HDMI-Monitor. Unter **Wayland** funktionieren die Gehäuselautsprecher bei vielen Nutzern.

**Vorgehen:** `sudo raspi-config` → **Advanced Options** → **A6 Wayland** → **Wayland** (oder labwc) wählen → Neustart. Beim Login die **Wayland-Session** wählen (nicht X11).

Details: **`docs/SWITCH_BACK_TO_WAYLAND.md`**

## Audio auf Gehäuselautsprecher umschalten (unter Wayland)

Wenn du unter Wayland bist und der Ton auf die **Gehäuselautsprecher** soll:

```bash
./scripts/set-audio-to-case-speakers.sh
```

Das Skript setzt den Standard-Ausgang auf HDMI-A-1 (107c701400), damit der Ton über Mediaboard/DSP1 an die Gehäuselautsprecher geht. Falls der HDMI-A-1 Sink noch nicht existiert, wird er automatisch aktiviert.

## Nach Neustart geht der Ton wieder zum Monitor (dauerhafte Lösung)

**Symptom:** Du setzt den Standard-Sink auf HDMI-A-1 (Gehäuselautsprecher), aber nach Neustart oder nach WirePlumber-Neustart ist wieder HDMI-A-2 (Monitor) der Standard – der Ton kommt aus dem Monitor statt aus den Gehäuselautsprechern.

**Ursache:** WirePlumber wählt beim Start den „verfügbaren“ HDMI-Port (HDMI-A-2 mit Monitor) als Standard. HDMI-A-1 gilt als „nicht verfügbar“ (kein Monitor angeschlossen – DSP1 hängt intern).

**Lösung (zwei Schritte):**

1. **WirePlumber-Priorität setzen**, damit HDMI-A-1 (Gehäuselautsprecher) als Standard-Sink gewählt wird:
   ```bash
   ./scripts/configure-wireplumber-hdmi-a1.sh
   ```
   (Erweitert die bestehende Konfiguration um Prioritäts-Regeln: HDMI-A-1 = hohe Priorität, HDMI-A-2 = niedrige Priorität.)

2. **HDMI-A-1 sehr früh + Autostart einrichten:**
   ```bash
   ./scripts/install-freenove-default-sink-autostart.sh
   ```
   Richtet ein:
   - **systemd-User-Service:** Läuft direkt nach WirePlumber (sehr früh) und aktiviert HDMI-A-1 sowie setzt ihn als Standard-Sink – bevor Anwendungen den Monitor-Sink übernehmen.
   - **Autostart:** Setzt den Standard-Sink nach Login nochmals (Fallback).
   Ohne diese frühe Aktivierung übernimmt oft der Monitor-Sink (HDMI-A-2) als Standard.

**Nach Schritt 1:** `systemctl --user restart wireplumber` (oder Neustart). Danach Neustart durchführen und testen.

**Sofort anwenden (ohne Neustart):**
```bash
./scripts/set-freenove-default-sink-on-login.sh 2
```

**Wieder entfernen:**
```bash
systemctl --user disable freenove-default-sink.service
rm -f ~/.config/systemd/user/freenove-default-sink.service ~/.config/autostart/pi-installer-freenove-default-sink.desktop
systemctl --user daemon-reload
```

---

## Schnell-Lösung: Komplette Reparatur

**WICHTIG:** Falls Audio nicht funktioniert und es früher funktioniert hat:

**Schritt 1: Repariere X11-Skripte (wenn unter X11):**
```bash
# X11-Skripte deaktivieren HDMI-A-1 automatisch - repariere das zuerst:
./scripts/fix-x11-hdmi-a1-deactivation.sh
```

**Schritt 2: HDMI-A-1 vollständig aktivieren (empfohlen bei „HDMI-A-1 ist disabled“):**
```bash
# Setzt cmdline.txt (video=HDMI-A-1:e + drm.edid_firmware) und config.txt [hdmi0]:
sudo ./scripts/enable-hdmi-a1-complete.sh
sudo reboot
```
**Nach dem Neustart unter X11:** `./scripts/fix-x11-hdmi-a1-deactivation.sh` ausführen, dann **abmelden und wieder anmelden** (sonst schaltet .xprofile HDMI-A-1 wieder aus).

**Schritt 3: Nach Neustart - Aktiviere HDMI-A-1 Sink:**
```bash
# Aktiviere HDMI-A-1 Sink (107c701400 / vc4hdmi0):
./scripts/activate-hdmi-a1-sink.sh

# Teste Audio:
./scripts/test-freenove-speakers-simple.sh
```

**Alternative: Teste ohne Monitor** (falls nach Neustart immer noch kein Ton):
```bash
# Viele Freenove Mediaboards extrahieren Audio nur ohne Monitor:
# Monitor abstecken, dann:
./scripts/test-freenove-speakers-simple.sh
```

**WICHTIG:** HDMI-A-1 kann nicht manuell aktiviert werden. Ein Neustart ist erforderlich, damit `cmdline.txt` wirksam wird. Siehe `docs/HDMI_A1_CANNOT_ENABLE.md` für vollständige Analyse.

**Warum EDID oft nicht wirkt:** Siehe `docs/WHY_EDID_CANNOT_BE_FORCED.md` – u.a. Optionen müssen **in** der ersten `[hdmi0]`-Sektion stehen; auf Pi 5 + Bookworm wird config.txt-EDID teils ignoriert, dann Alternative: `sudo ./scripts/fix-edid-via-kernel-cmdline.sh`.

**Nach der Reparatur - Audio testen:**
```bash
# Einfacher Test:
./scripts/test-freenove-speakers-simple.sh

# Oder ausführlicher Test:
./scripts/test-both-hdmi-sinks.sh
```

Diese Skripte testen beide HDMI-Sinks und fragen, ob der Ton aus den Gehäuselautsprechern kommt.

## Wie der Ton zu den Gehäuselautsprechern kommt (DSP1)

Die **Gehäuselautsprecher** (und die Kopfhörerbuchse) werden vom **DSP1** auf dem Freenove Mediaboard angesteuert. Der DSP1 bekommt sein Audiosignal vom Mediaboard, das **passiv** aus einem der HDMI-Ports des Pi das digitale Audio (IEC958) abgreift. Es gibt **kein separates „DSP1“-Gerät** in Linux – der Ton muss auf den **richtigen HDMI-Sink** geschickt werden (107c701400 oder 107c706400). Welcher Port intern mit dem Mediaboard/DSP1 verbunden ist, hängt vom Board ab; typisch ist **HDMI-A-1** (107c701400). Nur wenn dieser Sink als Standard genutzt wird, kann DSP1 das Signal an die Gehäuselautsprecher weitergeben.

**Fenster auf DSI/Gehäuse-Display:** Auf manchen Setups (Wayland, DSI + HDMI) kommt **nur dann** Ton aus den Gehäuselautsprechern, wenn das **Fenster** (Terminal, DSI-Radio, Browser usw.) auf dem **DSI-1 / Gehäuse-Display** läuft. Läuft das Fenster auf dem HDMI-Monitor, geht der Ton an den Monitor oder es kommt kein Ton. **Lösung:** Terminal oder App auf das DSI-Display (Gehäuse-TFT) ziehen, dann z. B. `paplay /usr/share/sounds/alsa/Front_Left.wav` ausführen. Siehe auch **docs/FREENOVE_TFT_DISPLAY.md** („Anzeige vs. Ton“).

## Sound nur aus Monitor – Recherche und Checkliste

**Offizielle Freenove-Dokumentation (fnk0100, fnk0107):**  
Beim Pi 5 gibt es keinen 3,5-mm-Ausgang mehr; Audio geht nur über HDMI. Das **Case Adapter Board** (Audio-Video Board) hat eine **Audio-Separationsschaltung**, die das Audiosignal aus dem HDMI-Signal extrahiert und an die 3,5-mm-Buchse sowie an die Lautsprecher-Anschlüsse (4 Ω, 3 W pro Kanal) ausgibt. Das Board ist über **zwei HDMI-Ports** an den Pi angebunden – welcher Port intern für die Gehäuselautsprecher genutzt wird, ist hardwareabhängig und in der Doku nicht festgelegt.

**Typische Gründe, warum Ton nur am Monitor ankommt:**

1. **Falscher HDMI-Sink als Standard:** Wenn der Standard-Sink der Monitor-Port (107c706400) ist, geht der Ton zum Monitor. Für Gehäuselautsprecher muss der Sink gesetzt werden, der mit dem internen Anschluss zum Case Adapter Board korrespondiert (oft 107c701400).  
   → `./scripts/activate-hdmi-a1-sink.sh` bzw. `pactl set-default-sink alsa_output.platform-107c701400.hdmi.hdmi-stereo`

2. **Fenster auf dem falschen Display (Wayland/DSI+HDMI):** Bei manchen Setups kommt Ton aus den Gehäuselautsprechern **nur**, wenn das Fenster (Terminal, DSI-Radio, Player) auf dem **DSI-1 / Gehäuse-Display** läuft. Läuft es auf dem HDMI-Monitor, geht der Ton an den Monitor.  
   → Terminal/App auf das DSI-Display (Gehäuse-TFT) ziehen und dort z. B. `paplay` testen.

3. **„Nur ohne Monitor“:** Einige Freenove-Boards extrahieren Audio nur, wenn **kein** HDMI-Monitor angeschlossen ist.  
   → Monitor abziehen, dann mit 107c701400 als Standard-Sink testen: `./scripts/test-audio-without-monitor.sh`

4. **Hardware:** Lautsprecher am SPEAKER-Header des Case Adapter Boards, FPC-Kabel Pi↔Board, Board fest eingesteckt. Kein separates „DSP1“-Gerät in Linux – das Board holt das Signal passiv aus HDMI.

**Kurz-Checkliste:** Standard-Sink 107c701400? → Fenster auf DSI? → Test ohne Monitor? → Lautsprecher/FPC geprüft? → Siehe Abschnitt „Von Null einrichten“ und „Problem: Ton geht nur zum HDMI-Monitor“ unten.

---

## Problem: Ton geht nur zum HDMI-Monitor, nicht zu den Gehäuselautsprechern

### Symptome

- HDMI-Audio ist aktiv (`wpctl status` zeigt HDMI-Sinks)
- Standard-Sink ist auf HDMI gesetzt
- Ton kommt nur aus dem HDMI-Monitor, nicht aus den Gehäuselautsprechern
- Beide HDMI-Ports (HDMI-A-1 und HDMI-A-2) zeigen dasselbe Verhalten
- **WICHTIG:** Monitor ist auf HDMI-A-2, aber Mediaboard könnte Audio von HDMI-A-1 extrahieren müssen

### Mögliche Ursachen

1. **Mediaboard extrahiert nicht korrekt:** Das Mediaboard sollte Audio passiv aus HDMI extrahieren, aber es funktioniert möglicherweise nur, wenn:
   - Kein Monitor angeschlossen ist
   - Ein bestimmter HDMI-Port verwendet wird
   - Eine spezielle Hardware-Konfiguration vorliegt

2. **Hardware-Problem:** 
   - Lautsprecher nicht richtig am "SPEAKER"-Header angeschlossen
   - Mediaboard nicht richtig über PCIe angeschlossen
   - Defektes Mediaboard

3. **Software-Konfiguration fehlt:**
   - Das Mediaboard benötigt möglicherweise eine spezielle Initialisierung
   - ALSA-Mixer-Einstellungen fehlen
   - Device Tree Overlay fehlt

### Lösungsansätze

#### 1. Prüfe Hardware-Verbindungen

- **Lautsprecher:** Sind die Lautsprecher korrekt am "SPEAKER"-Header des Case-Adapter-Boards angeschlossen?
- **PCIe-Verbindung:** Ist das Mediaboard korrekt über PCIe angeschlossen?
- **Flachbandkabel:** Ist das FPC-Kabel zwischen Pi 5 und Mediaboard richtig orientiert?
- **Monitor:** Unterstützt der Monitor HDMI-Audio? Prüfe mit `edid-decode` oder teste mit einem anderen Monitor

#### 1a. Aktiviere suspendierte HDMI-Sinks

Wenn beide HDMI-Sinks SUSPENDED sind (häufiges Problem):

```bash
# Aktiviere beide HDMI-Sinks:
./scripts/activate-hdmi-sinks.sh

# Oder manuell für jeden Sink:
pactl set-default-sink alsa_output.platform-107c701400.hdmi.hdmi-stereo
pactl set-sink-mute alsa_output.platform-107c701400.hdmi.hdmi-stereo 0
pactl set-sink-volume alsa_output.platform-107c701400.hdmi.hdmi-stereo 70%

# Audio abspielen (aktiviert den Sink):
paplay /usr/share/sounds/alsa/Front_Left.wav
```

#### 2. Aktiviere HDMI-A-1 als Audio-Sink (WICHTIG!)

**Problem:** Der Monitor ist auf HDMI-A-2 angeschlossen, aber das Mediaboard könnte Audio von HDMI-A-1 extrahieren müssen. HDMI-A-1 wird nicht als Sink angezeigt, weil dort kein Monitor angeschlossen ist.

**Lösung:** Aktiviere HDMI-A-1 auch ohne Monitor:

```bash
# Prüft und konfiguriert HDMI-A-1:
./scripts/test-hdmi-a1-for-speakers.sh

# Oder erzwinge HDMI-A-1:
./scripts/force-hdmi-a1-sink.sh

# Oder manuell in /boot/firmware/cmdline.txt ergänzen:
video=HDMI-A-1:e

# WICHTIG: Neustart erforderlich!
sudo reboot

# Nach Neustart testen:
./scripts/audio-test-after-reboot.sh
./scripts/diagnose-hdmi-a1-sink.sh
./scripts/test-both-hdmi-sinks.sh
```

**Befund:** 
- Card 0 (HDMI-A-1) existiert in `/proc/asound/cards` und `aplay -l`
- HDMI-A-1 ist als DRM-Device vorhanden, aber "disabled" (Status=connected, Enabled=disabled)
- WirePlumber erstellt keinen Sink für Card 0

**WICHTIGER BEFUND:** 
- Card 0 (HDMI-A-1) läuft im **IEC958-Modus (S/PDIF)**, nicht im PCM-Modus
- WirePlumber erstellt **keinen Sink für IEC958-Geräte** (nur PCM)
- Das Mediaboard könnte **IEC958-Signale direkt von Card 0 extrahieren**, auch ohne PipeWire-Sink

**Test:** Prüfe ob Card 0 direkt funktioniert:
```bash
# Prüfe Card 0 Format:
aplay -D hw:0,0 --dump-hw-params /dev/zero

# Teste IEC958-Direktausgabe:
./scripts/test-hdmi-a1-iec958-direct.sh
```

**Mögliche Lösung:** Das Mediaboard extrahiert IEC958-Signale automatisch aus HDMI, auch wenn kein PipeWire-Sink existiert. Audio muss dann direkt über ALSA im IEC958-Format ausgegeben werden.

**WICHTIG:** Card 1 (HDMI-A-2) läuft auch im IEC958-Modus, aber WirePlumber erstellt trotzdem einen Sink dafür, weil HDMI-A-2 "enabled" ist. Das bedeutet: **WirePlumber erstellt nur Sinks für "enabled" HDMI-Ports.**

**Lösung:** 
1. **WirePlumber-Konfiguration anpassen** (EMPFOHLEN):
   ```bash
   ./scripts/configure-wireplumber-hdmi-a1.sh
   ```
   Dies erstellt eine WirePlumber-Regel, die Card 0 auch bei "disabled" Display erkennt.

2. **HDMI-A-1 Display aktivieren** (Alternative):
   Siehe `docs/HDMI_A1_SINK_PROBLEM.md` für detaillierte Analyse.

---

#### 4. Beide HDMI-Sinks führen nur zum Monitor, nicht zu Gehäuselautsprechern

**Problem:** Beide HDMI-Sinks (`alsa_output.platform-107c701400.hdmi.hdmi-stereo` und `alsa_output.platform-107c706400.hdmi.hdmi-stereo`) führen Audio nur zum HDMI-Monitor, nicht zu den Gehäuselautsprechern.

**Mögliche Ursachen:**
1. **Mediaboard nicht richtig angeschlossen** (PCIe-Verbindung, FPC-Kabel)
2. **Mediaboard extrahiert nur ohne Monitor** (Hardware-Limitierung)
3. **Mediaboard benötigt spezielle Initialisierung**
4. **Hardware-Problem** (defektes Mediaboard, falsche Lautsprecher-Verbindungen)
5. **MUTE/Stummschaltung** (nur falls am Gehäuse vorhanden – nicht bei allen Freenove-Gehäusen)

**Lösungsschritte:**

1. **Prüfe Hardware-Verbindungen:**
   ```bash
   # Prüfe PCIe-Geräte:
   lspci | grep -i audio
   
   # Prüfe FPC-Kabel-Verbindung zwischen Pi 5 und Mediaboard
   ```

2. **Teste ohne Monitor:**
   ```bash
   # Monitor abstecken und testen:
   ./scripts/test-audio-without-monitor.sh
   ```

3. **Stummschaltung:** Falls dein Gehäuse einen MUTE-Schalter hat, prüfen ob er aus ist (viele Freenove-Gehäuse haben keinen)

4. **Prüfe Kernel-Logs:**
   ```bash
   sudo dmesg | grep -i "audio\|hdmi\|pcie\|freenove" | tail -50
   ```

5. **Siehe detaillierte Dokumentation:**
   - `docs/FREENOVE_MEDIABOARD_AUDIO_EXTRACTION.md` – Vollständige Analyse des Problems

**Hinweis:** Falls alle Software-Lösungen fehlschlagen, könnte es ein Hardware-Problem sein. Kontaktiere Freenove Support: https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi

**WICHTIG:** Siehe auch `docs/FREENOVE_MEDIABOARD_NO_AUDIO_FINAL.md` für eine vollständige Analyse dieses Problems.

**Wenn es früher funktioniert hat:** Setze WirePlumber-Konfiguration zurück:
```bash
./scripts/reset-wireplumber-audio-config.sh
```
Dies entfernt benutzerdefinierte Konfigurationen, die das Audio-Routing blockieren könnten.

**Wahrscheinlichste Lösung:** Teste ohne Monitor! Viele Freenove Mediaboards extrahieren Audio nur, wenn kein Monitor angeschlossen ist. Siehe `docs/FREENOVE_MEDIABOARD_NO_AUDIO_FINAL.md` – Schritt 1.

#### 3. Automatischer Test ohne Monitor

**Problem:** Ohne Monitor kann man nicht sehen, welche Befehle ausgeführt werden müssen.

**Lösung:** Automatisches Test-Skript verwenden:

```bash
# Monitor abstecken
# Dann automatischen Test starten (läuft ohne Benutzerinteraktion):
./scripts/test-audio-automatic.sh

# Nach dem Test Log-Datei prüfen:
cat ~/audio-test-*.log
```

Das Skript:
- Testet beide HDMI-Sinks automatisch
- Spielt Test-Töne ab
- Schreibt Ergebnisse in eine Log-Datei
- Erfordert keine Benutzerinteraktion

#### 4. Teste ohne HDMI-Monitor (manuell)

Das Mediaboard könnte nur funktionieren, wenn kein Monitor angeschlossen ist:

```bash
# Monitor abstecken
# Dann testen:
paplay /usr/share/sounds/alsa/Front_Left.wav
```

#### 4. Prüfe 3,5-mm-Ausgang

Teste den 3,5-mm-Ausgang am Case-Board:

```bash
# Kopfhörer in 3,5-mm-Buchse stecken
paplay /usr/share/sounds/alsa/Front_Left.wav
```

Wenn dort auch kein Ton kommt, ist HDMI-Audio wahrscheinlich nicht aktiv oder das Mediaboard funktioniert nicht.

#### 6. Prüfe ALSA direkt

Teste direkt über ALSA, um das Mediaboard zu umgehen:

```bash
# Teste Card 0 (HDMI-A-1)
aplay -D hw:0,0 /usr/share/sounds/alsa/Front_Left.wav

# Teste Card 1 (HDMI-A-2)
aplay -D hw:1,0 /usr/share/sounds/alsa/Front_Left.wav
```

#### 6. Prüfe Freenove-Dokumentation

Konsultiere die offizielle Freenove-Dokumentation:
- Repository: https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi
- Dokumentation: https://docs.freenove.com/projects/fnk0107/

#### 8. Kontaktiere Freenove-Support

Wenn nichts funktioniert, kontaktiere Freenove-Support:
- Email: support@freenove.com
- Website: https://www.freenove.com

### Bekannte Einschränkungen

- Das Mediaboard extrahiert Audio **passiv** aus HDMI
- Es gibt **keine** Software-API zur Steuerung der Lautsprecher
- Das Mediaboard erscheint **nicht** als separates Audio-Gerät im System
- Die Lautsprecher sind **nicht** über I2C steuerbar

### Weitere Informationen

Siehe auch:
- `docs/FREENOVE_AUDIO_OLED_SENSORS.md` – Allgemeine Audio-Dokumentation
- `docs/FREENOVE_COMPUTER_CASE.md` – Hardware-Zusammenbau
