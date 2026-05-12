# Qt (neueste Version) mit allen Modulen von der Website installieren

So installierst du eine Qt-Version inkl. Qt Creator und QML/Designer über den offiziellen Online-Installer.

**Hinweis:** Qt 6.10.x gilt nicht als produktionsreif. Für produktive Anwendungen im Installer eine **LTS-Version** wählen (z. B. **Qt 6.8 LTS** oder 6.6 LTS) statt der neuesten 6.10.x.

---

## 1. Qt-Account (kostenlos)

Falls noch nicht vorhanden:

- **Konto anlegen:** https://account.qt.io/
- Beim ersten Start des Installers wirst du nach E-Mail/Passwort gefragt (kostenloses Konto reicht für Open-Source-Nutzung).

---

## 2. Installer herunterladen (Linux x64)

**Offizielle Download-Seite:**

- https://www.qt.io/download-qt-installer

**Direktdownload Linux x64 (Stand: Installer 4.10.0):**

- https://d13lb3tujbc8s0.cloudfront.net/onlineinstallers/qt-online-installer-linux-x64-4.10.0.run

Ältere/andere Versionen:

- https://download.qt.io/official_releases/online_installers/

---

## 3. Installer ausführbar machen und starten

Im Terminal (z. B. im Download-Ordner):

```bash
chmod +x qt-online-installer-linux-x64-4.10.0.run
./qt-online-installer-linux-x64-4.10.0.run
```

Die grafische Oberfläche des Installers startet.

---

## 4. Im Installer: Anmeldung und Komponenten

1. **Anmeldung**  
   Mit Qt-Account (E-Mail/Passwort) anmelden. Ohne Konto sind nicht alle Komponenten wählbar.

2. **Installationspfad**  
   Voreinstellung z. B. `~/Qt` – kannst du so lassen oder anpassen.

3. **Komponenten-Auswahl**  
   Damit du **alle gewünschten Module** (inkl. QML, Designer) hast, **nicht** die Schnellauswahl „Qt for desktop development“ nehmen, sondern:

   - **„Custom installation“** (oder „Benutzerdefinierte Installation“) wählen.

4. **Unter „Custom installation“ auswählen:**

   | Kategorie | Auswählen |
   |-----------|-----------|
   | **Qt** | Die neueste **Qt 6.x** (z. B. Qt 6.10 oder aktuellste angezeigte Version). |
   | **Qt** → deine Qt 6.x | **Desktop** (z. B. „Qt 6.x.x for Desktop“, GCC 64-bit). |
   | **Qt** → deine Qt 6.x | **Qt Quick** (wichtig für QML und Designer). |
   | **Qt** → deine Qt 6.x | **Qt Quick Controls 2** (oder **Qt Quick Controls**). |
   | **Qt** → deine Qt 6.x | **Qt 5 Compatibility Module**, falls du ältere QML-Beispiele nutzen willst (optional). |
   | **Developer and Designer Tools** | **Qt Creator** (IDE inkl. QML-Designer). |
   | **Developer and Designer Tools** | **Qt Design Studio** (optional, für visuelles UI-Design). |

   Für „alle Module“: Unter der gewählten **Qt 6.x** alle sichtbaren Unterpunkte durchgehen und alles anhaken, was du brauchst (z. B. zusätzliche Qt-Module wie Multimedia, Network, etc.). Das vergrößert die Installation, deckt aber alle Bereiche ab.

5. **Installation starten**  
   Mit „Next“ / „Weiter“ durchgehen und am Ende „Install“ starten.

---

## 5. Nach der Installation: Qt Creator starten

Qt liegt typisch unter deinem Home-Verzeichnis, z. B.:

- `~/Qt/Tools/QtCreator/bin/qtcreator` (nur Qt Creator)
- oder über das **Qt Maintenance Tool** unter `~/Qt/MaintenanceTool` weitere Komponenten nachinstallieren.

**Starten:**

```bash
~/Qt/Tools/QtCreator/bin/qtcreator
```

Oder, falls Qt in einem anderen Pfad installiert wurde:

```bash
~/Qt/<Version>/gcc_64/bin/qmake   # nur zum Prüfen der Qt-Version
~/Qt/Tools/QtCreator/bin/qtcreator
```

**Optional:** Desktop-Verknüpfung anlegen (Menü „Qt“ / „Qt Creator“), je nach Installer-Setup.

---

## 6. Im Projekt: main.qml mit dem neuen Qt Creator öffnen

1. Qt Creator starten (wie oben).
2. **Datei** → **Projekt öffnen** → `apps/dsi_radio/qml/SabrinaTuner.qmlproject` öffnen (oder nur **Datei** → **Öffnen** → `main.qml`).
3. **Kit:** Beim ersten Mal ein Kit mit der **neu installierten Qt 6.x** auswählen (z. B. „Desktop Qt 6.x.x GCC“).
4. **Design-Button:** Sollte jetzt aktiv sein, da die QML-Module (QtQuick etc.) im gleichen Qt-Baum wie Qt Creator liegen.

---

## Kurzüberblick

| Schritt | Aktion |
|--------|--------|
| 1 | Qt-Account unter https://account.qt.io/ anlegen. |
| 2 | Von https://www.qt.io/download-qt-installer den Linux-Installer (.run) herunterladen. |
| 3 | `chmod +x …run` und `./…run` ausführen. |
| 4 | Anmelden, **Custom installation** wählen, **Qt 6.x** + **Qt Quick** + **Qt Creator** (und ggf. alle weiteren Module) auswählen, installieren. |
| 5 | Qt Creator mit `~/Qt/Tools/QtCreator/bin/qtcreator` starten. |
| 6 | Projekt `SabrinaTuner.qmlproject` oder `main.qml` öffnen und Design-Ansicht nutzen. |

Offizielle Doku (engl.): [Get and Install Qt](https://doc.qt.io/qt-6/get-and-install-qt.html), [Qt Online Installation](https://doc.qt.io/qt-6/qt-online-installation.html).

---

## Fehler: „QmakeOutputInstallerKey … ConsumeOutput … qmake needs to be called first“

Dieser Fehler (z. B. bei `qt.qt6.6102.linux_gcc_64`) tritt beim Online-Installer immer wieder auf. Nacheinander probieren:

### 1. Standard-Installationspfad verwenden

- **Nicht** in ein benutzerdefiniertes Verzeichnis mit Sonderzeichen oder eingeschränkten Rechten installieren.
- Voreinstellung **`~/Qt`** (z. B. `/home/deinname/Qt`) verwenden und Installation erneut starten.

### 2. Anderen Mirror verwenden

Der Installer lädt Komponenten von einem Server; manche Mirror-Varianten liefern fehlerhafte Pakete. Installer mit **anderem Mirror** starten (Pfad **ohne** `/online` und **ohne** Schrägstrich am Ende):

```bash
# Im Ordner mit dem .run-File:
./qt-online-installer-linux-x64-4.10.0.run --mirror "http://www.nic.funet.fi/pub/mirrors/download.qt-project.org"
```

Falls es damit scheitert, einen anderen Mirror probieren:

```bash
./qt-online-installer-linux-x64-4.10.0.run --mirror "http://ftp2.nluug.nl/languages/qt"
```

```bash
./qt-online-installer-linux-x64-4.10.0.run --mirror "http://qt.mirror.constant.com"
```

Dann erneut die gewünschten Komponenten auswählen und installieren.

### 3. Etwas ältere Qt-Version wählen

Falls der Fehler nur bei einer bestimmten Version (z. B. Qt 6.10.2) auftritt: In der **Custom installation** stattdessen eine **etwas ältere** Qt-6-Version wählen, z. B. **Qt 6.8 LTS** oder **Qt 6.6**. Qt Creator und QML/Designer funktionieren damit genauso; der Designer-Button wird mit der Installer-Qt-Installation aktiv.
