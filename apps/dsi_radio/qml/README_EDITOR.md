# Qt-Quick-Editor: Import-Fehler beheben

Wenn der Editor (Qt Creator o. ä.) meldet:
- **„Import QtQuick wurde nicht gefunden“**
- **„QML-Modul QtQuick.Window wurde nicht gefunden“**

und **QML2_IMPORT_PATH** bzw. Einstellungen in Qt Creator bringen nichts, hilft nur noch die Installation der System-Module (Qt Creator schaut fest auf `/usr/lib/.../qt6/qml`).

---

## Qt Creator so starten, dass QtQuick gefunden wird

Qt Creator **nicht** aus dem Anwendungsmenü starten, sondern über dieses Skript (setzt die QML-Import-Pfade):

```bash
cd /home/volker/piinstaller/apps/dsi_radio/qml
./start-qtcreator-for-qml.sh
```

Optional mit Datei: `./start-qtcreator-for-qml.sh main.qml`

Dann sollte „import QtQuick“ bzw. der davon abhängige QtQml-Fehler verschwinden.

---

## Lösung 1: System-QML-Module installieren (Voraussetzung)

**Im Terminal (mit sudo):**

```bash
sudo apt-get update
sudo apt-get install -y qml6-module-qtquick qml6-module-qtquick-window qml6-module-qtquick-controls qml6-module-qtquick-layouts
```

Danach **Qt Creator neu starten** und `main.qml` wieder öffnen – die Import-Fehler sollten weg sein. Es ist keine weitere Einstellung nötig.

---

## Lösung A: Projekt über .qmlproject öffnen (falls Ihr Qt Creator das unterstützt)

Im Ordner `qml` liegt **`SabrinaTuner.qmlproject`**. Diese Datei setzt den QML-Import-Pfad auf die PyQt6-Module der Venv.

**In Qt Creator:**
1. **Datei** → **Projekt öffnen** (oder „Öffnen“)
2. Zur Datei **`apps/dsi_radio/qml/SabrinaTuner.qmlproject`** navigieren und öffnen
3. Das Projekt wird geladen; die QML-Import-Pfade aus der .qmlproject gelten dann für alle QML-Dateien im Projekt
4. `main.qml` im Projekt öffnen – die Import-Fehler sollten verschwinden

Falls die Fehler bleiben: Qt Creator ggf. neu starten oder **Projekt** → **Projekt bereinigen / neu laden**.

---

## Lösung B: QML-Import-Pfad manuell in Qt Creator setzen

Die Venv enthält alle nötigen QML-Module (QtQuick, QtQuick.Window, Controls, …). Den Pfad im Editor als **QML Import Path** eintragen.

**Absoluter Pfad (anpassen falls anderes System/Python-Version):**
```
/home/volker/piinstaller/apps/dsi_radio/.venv/lib/python3.12/site-packages/PyQt6/Qt6/qml
```

**In Qt Creator:**
1. **Bearbeiten** → **Einstellungen** (oder **Projekt** → **Projekt-Einstellungen**)
2. Unter **Qt Quick** / **QML** nach **QML-Import-Pfad** / **Additional QML import paths** suchen
3. Diesen Pfad hinzufügen (oder als einzigen Eintrag verwenden)

**Oder für dieses Projekt:** In der Projektansicht Rechtsklick auf das Projekt → **QML-Import-Pfad** / **QML_IMPORT_PATH** und obigen Pfad eintragen.

**Per Umgebungsvariable (vor dem Start des Editors):**
```bash
export QML2_IMPORT_PATH="/home/volker/piinstaller/apps/dsi_radio/.venv/lib/python3.12/site-packages/PyQt6/Qt6/qml"
qtcreator
```

**Einzeiler aus dem Repo-Root (Pfad passt zur Venv):**
```bash
QML2_IMPORT_PATH="$(pwd)/apps/dsi_radio/.venv/lib/python3.12/site-packages/PyQt6/Qt6/qml" qtcreator apps/dsi_radio/qml/main.qml
```

Dann sollte der Editor QtQuick und QtQuick.Window aus der Venv finden.

---

## Hinweis: Qt Creator 13 und „import QtQuick“

Bei Qt Creator 13 (z. B. aus den Repos) werden die QML-Import-Pfade oft **nicht** aus Umgebungsvariablen (`QML2_IMPORT_PATH`, `QT_QML_IMPORT_PATH`) oder aus `.qmlproject` übernommen. Die Meldung „QtQuick wurde nicht gefunden“ / „QtQml … weil QtQuick nicht gefunden wurde“ kann dann **dauerhaft** angezeigt werden, obwohl die System-Module installiert sind und die **App einwandfrei läuft**.

**Folgen:** Nur die Anzeige im Editor ist falsch; **Build und Start** (z. B. `./scripts/start-dsi-radio-qml.sh`) sind davon nicht betroffen.

---

## Kurz

- **Lösung 1:** System-Pakete installieren (Voraussetzung, damit die App die QML-Module findet).
- **Qt Creator:** Starter-Skript oder Umgebungsvariablen beheben die Import-Anzeige unter Qt Creator 13 oft **nicht**; die roten Markierungen können bleiben.
- **Alternative:** `main.qml` in **Cursor** oder **VS Code** bearbeiten – keine Qt-Import-Prüfung, reines QML-Editing.
