# Freenove Computer Case Kit Pro – Software & Zusammenbau

## Zusammenbau – Erfahrungen & Hinweise

### Abstandshalter nicht überdrehen

Beim Anziehen der Abstandshalter **nicht zu fest** anziehen – das Gewinde kann abbrechen. Bei abgebrochenem Gewinde bleibt das Gehäuse dunkel (keine LEDs, keine Lüfter, kein Display).

### Flachbandkabel (FPC) – Orientierung

Das **Flachbandkabel** zwischen Pi 5 und Freenove Audio-Video-Board darf nicht verdreht werden. Anleitung Step 3:

> „Insert one end of the reverse straight cable to the RPi 5's PCIe interface (**The contacts should face the active cooler.**), then connect the other end to the PCIe IN interface on the Audio-Video Board (**The contacts should face the bottom.**)“

**Hinweis 1 – Kontaktseite vs. Isolationsseite:** Flachbandkabel haben eine Kontaktseite und eine Isolationsseite (schwarz). Wenn „Kontakte zeigen zum aktiven Cooler“ steht, ist genau das gemeint. Gleiches gilt für „Kontakte zeigen zum Board“ – dann sieht man von oben die **schwarze** Seite (Isolation). Bei verdrehtem Kabel: Gehäuse bleibt dunkel. **Lösung:** NVMe-Board ausbauen, FPC korrekt einstecken.

**Hinweis 2 – 2-, 3- und 4-adrige Kabel:** Die Kabel passen nur leicht in die Anschlüsse. Rückseite = glatte Seite, Vorderseite = ausgewölbte Kontakte. Wenn ein 4-adriges Kabel nicht passt (Stecker zu breit), das **andere** 4-adrige Kabel probieren – das passt dann.

### Boot: SD + NVMe oder nur NVMe

- **Hybrid (aktuell):** Boot von SD, Root von NVMe – siehe `docs/PATHS_NVME.md` und `docs/CLONE_ARCHITECTURE.md`.
- **Nur NVMe:** Muss noch ergänzt werden.

### Freenove-Software installieren

Installation von GitHub und mögliche Probleme: siehe **FAQ** in der App-Dokumentation.

---

## Software läuft nicht

Die Software für das **Freenove Computer Case Kit Pro** (Raspberry Pi 5) kommt aus dem Repository:

```bash
git clone https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi.git
```

Wenn die Anwendung nicht mehr startet, sind meist eine der folgenden Ursachen verantwortlich.

---

## 1. `python` vs. `python3` (sehr häufig)

Das Startskript `Code/run_app.sh` ruft **`sudo python app_ui.py`** auf. Unter aktueller Raspberry Pi OS zeigt `python` oft auf Python 2 (nicht mehr installiert) oder ist gar nicht gesetzt – die App braucht aber **Python 3**.

**Lösung:** In `Code/run_app.sh` die letzte Zeile anpassen:

```bash
# Vorher:
sudo python app_ui.py

# Nachher:
sudo python3 app_ui.py
```

Oder das Reparatur-Skript aus diesem Projekt nutzen (siehe unten).

---

## 2. Fehlende Python-Abhängigkeiten

Die GUI basiert auf **PyQt5**. Ohne installierte Pakete startet die App nicht oder bricht mit Import-Fehlern ab.

**Lösung (auf dem Pi):**

```bash
cd /pfad/zu/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi/Code
sudo apt update
sudo apt install -y python3-pyqt5 python3-smbus
pip3 install --user -r requirements.txt   # falls requirements.txt vorhanden
```

Typische Abhängigkeiten: `PyQt5`, `smbus` (oft als Systempaket `python3-smbus`).

---

## 3. Falscher Pfad im Desktop-Verknüpfung

Die Datei `Code/Freenove.desktop` enthält einen **fest eingetragenen Pfad**:

```ini
Exec=bash /home/pi/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi/Code/run_app.sh
Icon=/home/pi/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi/Code/Freenove_Logo.xpm
```

Wenn das Repo woanders liegt (z. B. unter einem anderen Benutzer oder in einem anderen Ordner), startet der Desktop-Link nichts.

**Lösung:**  
In `Freenove.desktop` die Pfade an den tatsächlichen Installationsort anpassen, z. B.:

```ini
Exec=bash /home/DEIN_USER/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi/Code/run_app.sh
Icon=/home/DEIN_USER/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi/Code/Freenove_Logo.xpm
```

Danach die Desktop-Datei wieder als ausführbar markieren und ggf. ins Benutzer-Menü kopieren:

```bash
cp Code/Freenove.desktop ~/.local/share/applications/
```

---

## 4. I2C / Hardware-Zugriff

Die Software spricht mit der Freenove-Erweiterungsplatine per **I2C** (`api_expansion.py`, `smbus`). Damit die App **ohne sudo** laufen kann (empfohlen wegen XDG_RUNTIME_DIR/Qt), den Benutzer in die Gruppe **i2c** aufnehmen:

```bash
sudo usermod -aG i2c "$USER"
```

Danach einmal abmelden und wieder anmelden (oder Neustart). Dann startet `run_app.sh` die App als normaler Benutzer und I2C-Zugriff funktioniert über die Gruppenrechte von `/dev/i2c-*`.

---

## 5. Anzeige / Wayland

Die Oberfläche ist eine **PyQt5-GUI**. Unter **Wayland** kann es vereinzelt zu Anzeigeproblemen kommen.

**Versuch:** Display-Backend erzwingen:

```bash
export QT_QPA_PLATFORM=xcb
./run_app.sh
```

Falls du per SSH ohne grafische Anmeldung startest, kann ein fehlendes Display den Start verhindern – dann die App auf dem Pi direkt im Desktop starten (oder mit gesetztem `DISPLAY`, z. B. `:0`).

### XDG_RUNTIME_DIR-Warnungen

- *«XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'»* – tritt auf, wenn die App mit **sudo** startet und die Session-Variablen fehlen.
- *«runtime directory '/run/user/1000' is not owned by UID 0»* – **sudo** (UID 0) darf das Verzeichnis von UID 1000 nicht nutzen (Rechte 0700).

**Lösung:** Die App **ohne sudo** starten. Dafür muss der Benutzer Zugriff auf I2C haben:

```bash
# Einmalig auf dem Pi: Benutzer in Gruppe i2c aufnehmen (danach ggf. abmelden/anmelden)
sudo usermod -aG i2c "$USER"
```

In `run_app.sh` wird die App dann als **aktueller Benutzer** gestartet (`python3 app_ui.py`), nicht als root. XDG_RUNTIME_DIR und DISPLAY bleiben gesetzt, die Qt-Warnungen entfallen. Im geklonten Repo unter PI-Installer ist das so in `Code/run_app.sh` umgesetzt.

---

## 6. Bildschirmrotation (Display drehen)

Wenn das Gehäuse **aufrecht steht**, das Display aber noch **seitlich** wirkt, die **physische Bildschirmdrehung** in der Raspberry-Pi-Konfiguration setzen.

### System-Drehung (config.txt)

Die Ausgabe wird in `/boot/firmware/config.txt` (bzw. `/boot/config.txt`) mit **display_rotate** gedreht:

- **0** = Normal (0°)
- **90** = 90° im Uhrzeigersinn (Case steht, Display war rechts gekippt)
- **180** = 180°
- **270** = 90° gegen Uhrzeigersinn

**Mit PI-Installer-Skript (auf dem Pi mit sudo):**

```bash
# PI-Installer-Verzeichnis: z.B. ~/Documents/PI-Installer oder ~/PI-Installer (auf dem Pi)
cd ~/PI-Installer   # oder dein tatsächlicher Pfad
# Einmal ausführen, danach Neustart: sudo reboot
sudo ./scripts/freenove-set-display-rotate.sh 90
# oder interaktiv:
sudo ./scripts/freenove-set-display-rotate.sh
```

**Manuell:** In `config.txt` die Zeile `display_rotate=1` (für 90°) setzen bzw. anpassen, dann Neustart.

### DSI unter Wayland: 90° nach links (nur DSI, nicht HDMI)

Wenn du **Wayland** mit **DSI + HDMI** nutzt (z. B. Pi 5, Wayfire/Labwc), dreht `display_rotate` in config.txt **alle** Ausgaben. Für **nur das DSI-Display** 90° nach links (Portrait) nutzt du die **Wayland-Output-Rotation**:

- **Skript (als Benutzer der Wayland-Session, aus dem PI-Installer-Verzeichnis):**  
  `cd ~/PI-Installer && ./scripts/freenove-dsi-rotate-portrait.sh`  
  Setzt für DSI-1 **transform 90** in Kanshi und wayfire.ini. Danach einmal abmelden/anmelden oder Kanshi neu starten.
- **Sofort testen (bis zum Session-Neustart):**  
  `wlr-randr --output DSI-1 --transform 90`

Wenn du das Skript **fix-gabriel-dual-display-wayland.sh** nutzt, ist DSI-Rotation 90° dort bereits eingebaut (Kanshi + wayfire.ini). Ausführung (auf dem Pi): `cd ~/PI-Installer && sudo ./scripts/fix-gabriel-dual-display-wayland.sh`

### Fenster-Layout in der Freenove-App (Portrait / Landscape)

In der Freenove-App unter **Settings** gibt es den Button **„Portrait ↔ Landscape“** (ehemals „Rotate UI“). Er wechselt nur das **Fensterlayout** (Hochformat 480×740 / Querformat 800×420), nicht die Hardware-Drehung. Nach der System-Drehung (display_rotate) ggf. diese Taste nutzen, damit die Anzeige den Bildschirm ausfüllt.

---

## 7. Erweiterungen mit anderen teilen

Die Anpassungen (python3, kein sudo, XDG_RUNTIME_DIR, Portrait/Landscape-Label, Skripte, Doku) liegen im **PI-Installer**-Projekt. Andere Nutzer desselben Case können sie so nutzen:

### Option A: PI-Installer klonen

PI-Installer klonen – darin liegt der angepasste Freenove-Ordner sowie die Skripte und die Doku:

```bash
git clone https://github.com/DEIN_ORG/PI-Installer.git
cd PI-Installer
# Freenove-Code: Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi/
# Skripte: scripts/fix-freenove-computer-case.sh, scripts/freenove-set-display-rotate.sh
# Doku: docs/FREENOVE_COMPUTER_CASE.md
```

Auf dem Pi: Reparatur-Skript und ggf. Display-Rotation ausführen (siehe Abschnitte 6 und 8).

### Option B: Nur die Änderungen weitergeben (Patch)

Wenn jemand bereits das **Original-Freenove-Repo** geklont hat, können die PI-Installer-Änderungen als **Patch** angewendet werden. Im PI-Installer-Repo (nach dem Klonen):

```bash
cd Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi
git diff origin/main -- Code/ > ../freenove-pi-installer.patch
```

Empfänger (im eigenen Freenove-Klon):

```bash
cd Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi
git apply /pfad/zum/freenove-pi-installer.patch
```

Die Skripte `fix-freenove-computer-case.sh` und `freenove-set-display-rotate.sh` sowie die Doku liegen nur im PI-Installer-Repo und müssen ggf. separat geteilt werden (z. B. durch Weitergabe des Repos oder der `scripts/`- und `docs/`-Dateien).

---

## 8. Reparatur-Skript aus dem PI-Installer-Projekt

Im Ordner `scripts/` liegt ein Hilfsskript, das auf dem **Raspberry Pi** ausgeführt werden kann (nach dem Klonen des Freenove-Repos):

```bash
# Aus dem PI-Installer-Verzeichnis (z.B. cd ~/PI-Installer auf dem Pi):
./scripts/fix-freenove-computer-case.sh
# Optional mit eigenem Freenove-Pfad:
./scripts/fix-freenove-computer-case.sh /home/pi/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi
```

Das Skript:

- ersetzt in `Code/run_app.sh` `python` durch `python3`,
- passt optional die Pfade in `Freenove.desktop` an,
- gibt Hinweise zur Installation von PyQt5 und smbus.

---

## 9. Manueller Test

Zum schnellen Prüfen direkt im Code-Verzeichnis:

```bash
cd Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi/Code
sudo python3 app_ui.py
```

Fehlermeldungen (z. B. „No module named 'PyQt5'“ oder „No module named 'smbus'“) zeigen, was noch installiert werden muss.

---

## Kurzfassung

| Problem | Maßnahme |
|--------|----------|
| „python: command not found“ / Python 2 | In `run_app.sh`: `python` → `python3` |
| Import Fehler PyQt5/smbus | `sudo apt install python3-pyqt5 python3-smbus` |
| Desktop-Link startet nichts | Pfade in `Freenove.desktop` anpassen |
| I2C/Hardware-Fehler | Benutzer in Gruppe `i2c`: `sudo usermod -aG i2c $USER`, dann ohne sudo starten |
| Kein Fenster / Wayland | `QT_QPA_PLATFORM=xcb` setzen oder am Pi-Desktop starten |
| Display steht „falsch“ (Case aufrecht) | **Wayland (DSI+HDMI):** Skript `freenove-dsi-rotate-portrait.sh` (90° nach links, nur DSI). **Global:** `display_rotate` in config.txt oder `freenove-set-display-rotate.sh`, dann Neustart. |
| Fenster füllt Bildschirm nicht | In der App unter Settings: „Portrait ↔ Landscape“ nutzen |

Repository: https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi
