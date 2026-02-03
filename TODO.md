sudo systemctl disable nginx
Ergänze alle ok, jetzt alles nach githubsudo systemctl stop nginxstartx
# PI-Installer – ToDo-Liste

Übersicht aller geplanten Verbesserungen und Features. Abhaken mit `[x]`.

---

## 1. UI: Kontrast der Kategorie-Überschriften ✅

- [x] **Dashboard, Assistent, Voreinstellungen:** Überschriften haben schlechten Kontrast (hell weiß auf grauweiß).
- [x] **Umsetzung:** Buchstaben weiß mit dunkelgrauem Rahmen darstellen.
- [x] Überschrift mit Schatten hinterlegen (gleicher Stil wie beim aktiven Menü-Button).

---

## 2. WLAN ✅

- [x] Verbindung zu **hinzugefügten WLAN-Netzwerken** herstellen können (nicht nur hinzufügen).
- [x] Control Center → WLAN: Bei konfigurierten Netzwerken Button „Verbinden“; Backend: `wpa_cli select_network` + API `/api/control-center/wifi/connect`.

---

## 3. Gestoppte Services wieder starten ✅

- [x] Gestoppte Dienste wie **SSH, VNC** und andere wieder **starten** können (neben Stoppen/Neustart).
- [x] Control Center → SSH: „SSH starten“-Button wenn aktiviert aber gestoppt; VNC: „VNC starten“-Button wenn gestoppt. Backend: `systemctl start ssh` / `vncserver-x11-serviced`.

---

## 4. Bildwiederholfrequenz ✅

- [x] Geänderte **Bildwiederholfrequenz** wird augenscheinlich nicht übernommen – prüfen und beheben.
- [x] Beim Übernehmen der Display-Einstellungen wird die Bildwiederholfrequenz immer mitgesendet (ausgewählter Wert oder Standard des Modus).

---

## 5. CPU/Grafik-Hinweise (Dashboard) ✅

- [x] **Hinweis anzeigen:**
  - Welche **CPU** ist verbaut?
  - Welche **MHz-Zahl** wird genutzt, welche ist empfohlen?
  - Welche **Grafikkarte** wird genutzt?
  - Sind zwei verbaut (CPU + Grafikkarte) – wie viel **Speicher** sollte man wem zuweisen (wenn überhaupt)?
  - Gibt es **Richtwerte für die Erhöhung der Spannung**?
- [x] **Dashboard:** Karte „CPU & Grafik“ zeigt **jede CPU** und **jede gefundene GPU** (Modell, MHz, Speicher). Daten aus `/api/system-info` (hardware.cpus, hardware.gpus); Backend: /proc/cpuinfo, vcgencmd (Pi), lspci (GPUs).
- [x] **Raspberry Pi Config:** Nur noch Hinweis auf Dashboard sowie Speicheraufteilung und Spannungserhöhung (over_voltage).

---

## 6. Raspberry Pi Config nur auf Pi ✅

- [x] **Raspberry Pi Config** ausblenden, wenn der PI-Installer **nicht auf einem Raspberry Pi** läuft.

---

## 7. Monitoring-Installation: SUDO & Auswahl ✅

- [x] Beim Monitoring wird gesagt, dass das **SUDO-Passwort** erforderlich sei – **Eingabemaske erscheint nicht**; beheben.
- [x] Aktuell scheint nur **„alle drei Programme installieren“** möglich – **Auswahl** ermöglichen (einzeln wählbar: z. B. Prometheus, Grafana, Node Exporter).
- [x] **Umsetzung:** SudoPasswordModal statt prompt(); Checkboxen für Node Exporter, Prometheus, Grafana; nur ausgewählte Komponenten installieren.

---

## 8. Musikbox: Internetradio, Streaming, Übersicht ✅

- [x] **Internetradio** und **Streamingdienste** als einrichtbare Optionen ergänzen.
- [x] **Kurzer Hinweis** zu den Music-Servern: was können sie, und ob dahinter **Bezahldienste** stecken.
- [x] **Umsetzung:** Checkboxen Internetradio (Mopidy mopidy-internetarchive), Streaming; Info-Box zu Music-Servern und Bezahldiensten; Backend enable_internetradio, enable_streaming.

---

## 9. Systemdaten nach Neustart: alle Sensoren/Schnittstellen ✅

- [x] Nach Neustart sollen **alle** relevanten Daten und Schnittstellen sichtbar sein:
  - **Mehrere Temperatursensoren** → alle anzeigen.
  - **Mehrere Laufwerke** → alle anzeigen.
  - **Mehrere Lüfter** → alle anzeigen.
  - **Mehrere Displays** → alle anzeigen.
- [x] **Umsetzung:** Backend /api/system-info liefert sensors, disks, fans, displays; Dashboard-Karte „Sensoren & Schnittstellen“.

---

## 10. Peripherie-Scan („Assimilation“) ✅

- [x] **Scan nach verwendeter Peripherie:** besondere Grafikkarten, Tastaturen, Mäuse, Headsets, Webcams – prüfen ob **Treiber** passen und Geräte **funktionieren**.
- [x] **Start-Text:** „Beginne mit der Assimilation des Systems!“  
  **Untertitel:** „Widerstand ist zwecklos.“
- [x] **Ladebalken** animieren bis zum erwarteten Abschluss der „Maßnahme“.
- [x] **Umsetzung:** Neue Seite „Peripherie-Scan (Assimilation)“; API /api/peripherals/scan (lspci, lsusb, /proc/bus/input/devices); Start-Text, animierter Ladebalken, Ergebnisliste.

---

## 11. Dashboard: Status DEV, Webserver, Musikbox ✅

- [x] **DEV-Umgebung:** Im Dashboard anzeigen – wie viele Teile installiert, ob **Grundbetrieb** möglich (z. B. Compiler/IDE lauffähig).
- [x] **Webserver:** Anzeigen ob Webserver läuft, ob **Webseiten** schon erreichbar sind.
- [x] **Musikbox:** Gleiches – Installationsstand und ob **Grundbetrieb** (Abspielen) möglich ist.

---

## 12. Hausautomation: Suche & Empfehlung ✅

- [x] **Runder roter Start-Button** zum **Suchen nach Elementen im Haus** (Geräte/Integrationen).
- [x] **Empfehlung**, welches System man nehmen sollte; **Beschreibung**, was die Systeme können und zu welchen **Anbietern** sie kompatibel sind.
- [x] Bei **Start der Suche:**  
  - Text: **„Das Haus wird assimiliert!“**  
  - Untertitel: **„Widerstand ist zwecklos!“**  
  (wenn automatische Suche nach Komponenten möglich ist.)

---

## 13. Entwicklungsumgebung: QT/QML & mehr ✅

- [x] **Installationsoption ergänzen:** **QT, QML** und dazugehörige Pakete.
- [x] Prüfen: Weitere **Programmiersprachen** sinnvoll? Fehlen **Entwicklungsumgebungen** oder **weitere Programme & Tools**?

---

## 14. PI-Installer auf anderen Systemen

- [ ] **Kann der PI-Installer** auf einem anderen System (nicht nur Raspberry Pi) als **Linux-Installer/Konfigurator** genutzt werden?  
  - Anforderung klären, Konzept/Umfang dokumentieren oder eingrenzen.

---

## Legende

| Symbol | Bedeutung     |
|--------|----------------|
| `[ ]`  | Offen          |
| `[x]`  | Erledigt       |

---

*Erstellt: Januar 2026 | Projekt: PI-Installer*
