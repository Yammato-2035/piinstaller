# Qt Creator: Wo genau den QML-Import-Pfad eintragen

Damit Qt Creator **QtQuick**, **QtQuick.Controls**, **QtQuick.Layouts** und **QtQuick.Window** findet, gibt es nur wenige offiziell dokumentierte Stellen. Für unser **reines QML-Projekt** (`.qmlproject`, kein qmake/CMake-Build) sind das:

---

## 1. In der Projektdatei (bereits erledigt)

**Datei:** `SabrinaTuner.qmlproject`  
**Eigenschaft:** `importPaths` (Liste von Pfaden)

Die Pfade stehen bereits in der Datei. Qt Creator **sollte** sie beim Öffnen des Projekts auswerten. Wenn er es nicht tut (z. B. Qt Creator 13), die folgenden Schritte nutzen.

**Offizielle Doku:**  
[Using QML modules with plugins – Qt Quick UI Prototype projects](https://doc.qt.io/qtcreator/creator-qml-modules-with-plugins.html):  
*"For Qt Quick UI Prototype projects (.qmlproject), specify the path … in the .qmlproject file … as a value of the **importPaths** variable."*

---

## 2. Projekt-Umgebung (Environment) – empfohlener Zusatz

Hier kannst du **pro Projekt** Umgebungsvariablen setzen. Einige Qt-Creator-Versionen nutzen sie auch für die QML-Code-Analyse.

**Exakter Weg in Qt Creator:**

1. Links auf **„Projekte“** klicken (oder **Fenster** → **Ansichten** → **Projekte**).
2. Oben unter den Tabs **„Build & Run“** sicherstellen, dass dein **Kit** (z. B. „Desktop Qt 6.4.2 GCC“) ausgewählt ist.
3. In der linken Spalte unter **„Build & Run“** den Eintrag **„Projekt“** bzw. den Projektnamen **„SabrinaTuner“** auswählen (nicht „Build“, „Run“ oder ein Unterpunkt davon).
4. Oben rechts erscheinen Tabs: **„Editor“**, **„Build“**, **„Run“**, **„Deploy“** usw.  
   Nach einem Bereich **„Umgebung“** / **„Environment“** / **„Projektumgebung“** suchen.  
   Falls er direkt unter dem Projektnamen liegt: Dort **„Umgebung ändern“** / **„Change“** (bei Environment) klicken.
5. In der Umgebungsliste **„Hinzufügen“** / **„Add“** wählen und eintragen:
   - **Name:** `QML2_IMPORT_PATH`  
   - **Wert:** `/usr/lib/x86_64-linux-gnu/qt6/qml`
6. Optional zweite Variable (für Untermodule):
   - **Name:** `QT_QML_IMPORT_PATH`  
   - **Wert:** `/usr/lib/x86_64-linux-gnu/qt6/qml`
7. Übernehmen (OK / Apply).

**Falls „Umgebung“ nicht unter dem Projekt sichtbar ist:**

- **Projekte** → **Projekteinstellungen** (oder Doppelklick auf den Projektnamen in der Projektansicht).  
- In den Einstellungen nach **„Projektumgebung“** / **„Project Environment“** suchen und dort die gleichen Variablen anlegen.

**Offizielle Doku:**  
[Specify the environment for projects](https://doc.qt.io/qtcreator/creator-how-set-project-environment.html):  
*"To change the system environment for a project … select **Projects > Project Settings > Project Environment**."*

---

## 3. Build-Umgebung (Build Environment)

Die **Build**-Umgebung wird für reine QML-Projekte ohne echten Build oft nicht genutzt. Falls dein Projekt trotzdem ein Kit mit „Build“-Schritten hat, kannst du die gleichen Variablen auch hier setzen:

1. **Projekte** → links **„Build“** (unter Build & Run) auswählen.
2. Rechts nach **„Build-Umgebung“** / **„Build Environment“** suchen.
3. **„Umgebung ändern“** / **„Change“** → **„Hinzufügen“**:
   - `QML2_IMPORT_PATH` = `/usr/lib/x86_64-linux-gnu/qt6/qml`
   - ggf. `QT_QML_IMPORT_PATH` = `/usr/lib/x86_64-linux-gnu/qt6/qml`

**Doku:**  
[Specify the environment for projects – Specify the build environment](https://doc.qt.io/qtcreator/creator-how-set-project-environment.html):  
*"To specify the build environment … go to **Projects > Build Settings** and select **Build Environment**."*

---

## 4. QML/JS-Code-Model zurücksetzen

Nach jeder Änderung an Import-Pfaden oder Umgebung:

1. **Werkzeuge** → **QML/JS** → **Code-Model zurücksetzen**  
   (engl.: **Tools** → **QML/JS** → **Reset Code Model**)
2. Kurz warten; danach sollten die Imports neu ausgewertet werden.

**Offizielle Doku:**  
[Using QML modules with plugins](https://doc.qt.io/qtcreator/creator-qml-modules-with-plugins.html):  
*"If Qt Creator cannot find the new QML module, build the project and then go to **Tools > QML/JS > Reset Code Model** to reset the code model."*

---

## 5. Kein eigenes „QML-Import-Pfad“-Feld in der Doku

In der offiziellen Qt-Creator-Dokumentation gibt es **kein** separates GUI-Feld namens „QML-Import-Pfad“ oder „Additional QML import paths“ unter **Bearbeiten** → **Einstellungen**.  
Die Doku beschreibt nur:

- **qmake:** `QML_IMPORT_PATH` in der **.pro**-Datei  
- **CMake:** `set(QML_IMPORT_PATH ...)` im **CMakeLists.txt**  
- **.qmlproject:** **importPaths** in der **.qmlproject**-Datei  

Für reine QML-Projekte ohne qmake/CMake bleiben daher: **importPaths** in der Datei, **Projekt-/Build-Umgebung** (Environment) und **Code-Model zurücksetzen**.

---

## 6. Projekt als CMake öffnen (oft zuverlässiger)

Qt Creator liest **QML_IMPORT_PATH** bei **CMake-Projekten** aus der Konfiguration – das wird oft beachtet, auch wenn .qmlproject ignoriert wird.

**Vorgehen:**

1. Projekt **schließen** (Datei → Alle schließen / Projekt schließen).
2. **Datei** → **Projekt öffnen** (oder „Öffnen“).
3. **Nicht** `SabrinaTuner.qmlproject` wählen, sondern **`CMakeLists.txt`** im Ordner `apps/dsi_radio/qml/`.
4. Kit auswählen (z. B. „Desktop Qt 6.4.2 GCC“), Konfiguration durchlaufen lassen.
5. Im Projektbaum **`main.qml`** öffnen (unter dem geöffneten Ordner).
6. **Werkzeuge** → **QML/JS** → **Code-Model zurücksetzen**.

Die `CMakeLists.txt` in diesem Ordner setzt bereits `QML_IMPORT_PATH` auf den System-Qt-Pfad. Es wird **nichts gebaut** – die Datei dient nur dazu, dass Qt Creator den QML-Pfad übernimmt.

---

## Kurz: Konkrete Reihenfolge für SabrinaTuner

**Variante A – Projekt als CMake öffnen (zuerst probieren):**  
Projekt schließen → **Datei** → **Projekt öffnen** → **`CMakeLists.txt`** (nicht .qmlproject) im Ordner `qml` wählen → Kit wählen → `main.qml` öffnen → **Werkzeuge** → **QML/JS** → **Code-Model zurücksetzen**.

**Variante B – .qmlproject mit Umgebung:**  
1. **Projekte** → Projekt **SabrinaTuner** auswählen → **Projekteinstellungen** / **Project Settings**.
2. **Projektumgebung** / **Project Environment** suchen → **Umgebung ändern**.
3. Hinzufügen: `QML2_IMPORT_PATH` = `/usr/lib/x86_64-linux-gnu/qt6/qml` (und optional `QT_QML_IMPORT_PATH` gleich).
4. Übernehmen, dann **Werkzeuge** → **QML/JS** → **Code-Model zurücksetzen**.
5. `main.qml` erneut öffnen.

---

## Dokumentationslinks (Referenz)

| Thema | URL |
|-------|-----|
| FAQ: Rote Linie unter QML-Import | https://doc-snapshots.qt.io/qtcreator-master/creator-faq.html (Abschnitt „QML and Qt Quick Questions“) |
| QML-Module mit Plugins / importPaths | https://doc.qt.io/qtcreator/creator-qml-modules-with-plugins.html |
| Projektumgebung setzen | https://doc.qt.io/qtcreator/creator-how-set-project-environment.html |
| Build-Umgebung | gleiche Seite, Abschnitt „Specify the build environment“ |

Alle Links führen auf die offizielle Qt Creator Documentation (doc.qt.io).

---

## Online-Installer-Qt ist installiert, aber „wird nicht gefunden“

Wenn du **Qt aus dem Online-Installer** (z. B. unter ~/Qt) nutzt und die Imports trotzdem rot sind:

1. **Richtiges Kit verwenden**  
   Das Projekt muss ein Kit nutzen, dessen **Qt-Version aus ~/Qt** kommt, nicht aus /usr.
   - **Projekte** (links) → oben **„Build & Run“** → unter **„Kit“** prüfen, welches ausgewählt ist.
   - Es muss z. B. **„Desktop Qt 6.10.2 GCC“** (oder deine Version) sein, **nicht** „Desktop Qt 6.4.2 GCC“ (System).
   - Welche Qt wo liegt: **Bearbeiten** → **Einstellungen** → **Kits** → **Qt-Versionen**: Die zum Online-Installer zeigt auf einen Pfad wie `~/Qt/6.10.2/gcc_64/bin/qmake`, die System-Qt auf `/usr/...`.

2. **Projekt als CMake öffnen (nicht .qmlproject)**  
   Sonst zählt oft die alte Konfiguration.
   - Projekt schließen.
   - **Datei** → **Projekt öffnen** → **`CMakeLists.txt`** im Ordner `apps/dsi_radio/qml/` wählen.
   - Beim Konfigurieren das **Kit mit Qt aus ~/Qt** wählen (siehe oben).
   - Danach **`main.qml`** öffnen, **Werkzeuge** → **QML/JS** → **Code-Model zurücksetzen**.

3. **Alte Konfiguration verwerfen**  
   Wenn das Projekt vorher mit System-Qt-Kit geöffnet war:
   - Projekt schließen.
   - Im Ordner `apps/dsi_radio/qml/` den Unterordner **`.qtcreator`** (falls vorhanden) und ggf. **`CMakeCache.txt`** / **`CMakeFiles`** im Build-Verzeichnis löschen.
   - CMakeLists.txt wieder öffnen und das **Kit mit Qt aus ~/Qt** wählen.

---

## Wenn es gar nicht geht

Bei **Qt Creator 13** aus den Repos mit **System-Qt 6.4.2** kann die QML-Import-Anzeige trotz aller Einstellungen fehlerhaft bleiben – bekanntes Verhalten.

**Pragmatische Alternativen:**

- **QML in Cursor/VS Code bearbeiten:** `main.qml` hier im Projekt öffnen. Keine Qt-Import-Prüfung, aber volles Editing (x, y, width, height usw. von Hand setzen).
- **Rote Markierungen ignorieren:** Die **App** läuft mit `./scripts/start-dsi-radio-qml.sh` korrekt; nur die Anzeige im Qt Creator ist falsch.
