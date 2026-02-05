# PI-Installer: Analyse der größten Hürden

*Erstellt im Rahmen des Transformationsplans "Raspberry Discovery Box".*

## 1. Installation & Einstieg

### Hürde: Kein One-Click-Installer
- **Aktuell:** Nutzer muss manuell: Repository klonen, Python venv, pip install, npm install, zwei Terminals starten.
- **Dokumentation:** INSTALL.md, QUICKSTART.md, README.md – alle verlangen explizit **Python 3.12** und mehrere Befehle.
- **Folge:** "Anna, die Lehrerin" scheitert bereits am Einstieg; sie will nur Nextcloud, nicht Git/Python/Node verstehen.

### Hürde: Python-Version als Deal-Breaker
- **Aktuell:** QUICKSTART.md und README betonen "Python 3.12 erforderlich", "NICHT Python 3.13!".
- **Backend:** `requirements.txt` nutzt Versionen wie `fastapi>=0.100`, `uvicorn[standard]>=0.24` – unter älteren Python-Versionen können pydantic/fastapi-Builds scheitern.
- **Folge:** Auf vielen Pis und älteren Debian-Installationen ist nur Python 3.9–3.11 standardmäßig vorhanden; Nutzer bricht ab oder sucht stundenlang nach Python 3.12.

### Hürde: Kein systemd-Service im Repo
- **Aktuell:** INSTALL.md verweist auf `pi-installer.service` und `sudo cp pi-installer.service ...`, aber **die Datei existiert nicht** im Repository.
- **Folge:** Nutzer kann "wie dokumentiert" keinen dauerhaften Dienst einrichten.

---

## 2. Architektur & Abhängigkeiten

### Hürde: Zwei getrennte Prozesse (Backend + Frontend)
- **Aktuell:** Backend (Python/uvicorn :8000) und Frontend (Node/Vite :3001) müssen beide laufen; Start über `start.sh` oder manuell zwei Terminals.
- **Folge:** Einsteiger verstehen nicht "warum zwei Programme", und vergessen oft eines zu starten oder schließen versehentlich ein Terminal.

### Hürde: Node.js nur für Entwicklung
- **Aktuell:** Frontend wird mit `npm run dev` gestartet; für Produktion wäre Build (`npm run build`) + statisches Ausliefern (z. B. über Backend oder Nginx) nötig – nicht einheitlich dokumentiert.
- **Folge:** Unklarheit, ob nach "Installation" dauerhaft `npm run dev` laufen muss oder ob es eine "Production"-Variante gibt.

### Hürde: Monolithisches Backend
- **Aktuell:** `backend/app.py` ist sehr groß (tausende Zeilen); Logik für Auth, Logging, Module, API in einer Datei.
- **Folge:** Schwer wartbar; Erweiterung um "App-Store" und klare Trennung (core / services / apps) ohne Refactoring kaum möglich.

---

## 3. UX & Zielgruppe

### Hürde: Sprache und Begriffe für Admins
- **Aktuell:** Oberfläche und Docs sprechen von "Modulen", "Backend", "Frontend", "venv", "Port 8000/3001".
- **Folge:** Einsteiger wie Anna oder Markus wollen "Apps installieren" und "alles läuft" – nicht technische Konzepte.

### Hürde: Kein First-Run-Wizard
- **Aktuell:** Beim ersten Start landet man direkt im Dashboard ohne geführte Einrichtung (Netzwerk, Passwort, erste App).
- **Folge:** Kein geführtes "Lass uns deinen Pi einrichten!" – Nutzer muss selbst wissen, wo er anfängt.

### Hürde: Fehlermeldungen ohne Hilfe
- **Aktuell:** Viele API-/Installationsfehler enden mit technischen Meldungen oder "Installation fehlgeschlagen" ohne Reparaturvorschlag.
- **Transformationsplan:** "Huch, das hat nicht geklappt. Lass es uns zusammen reparieren!" – dafür fehlt noch die konkrete Umsetzung (Assistent, Auto-Fix-Optionen).

---

## 4. Pi-spezifische & Betrieb

### Hürde: RAM/Performance nicht im Fokus
- **Aktuell:** README nennt "4GB+ RAM"; viele Nutzer haben Pi 4 mit 2GB oder ältere Geräte.
- **Folge:** Keine klaren Hinweise wie "Diese App braucht 1GB – dein Pi hat 2GB" oder leichte Alternativen; Risiko von Überlastung und Frust.

### Hürde: Kein einheitlicher Zugriff nach Installation
- **Aktuell:** Dokumentation zeigt localhost:3001 bzw. LAN-IP:3001 – kein festes "Öffnen Sie http://pi-installer.local" (mDNS) oder klare Anleitung, wie man die Oberfläche dauerhaft erreicht.
- **Folge:** Nutzer vergisst die IP oder fragt sich "wie komme ich wieder rein?".

---

## 5. Priorisierte Handlungsempfehlungen

| Priorität | Hürde | Maßnahme (Phase 1) |
|-----------|--------|---------------------|
| P0 | Kein Single-Script-Installer | `create_installer.sh` implementieren (inkl. Python-Erkennung, Node optional, systemd, klare Abschlussmeldung) |
| P0 | Fehlende systemd-Datei | `pi-installer.service` im Repo anlegen und vom Installer verwenden |
| P1 | Python 3.12 Pflicht | requirements.txt und Docs auf 3.9+ ausrichten; Fallback/Warnung wenn < 3.12 |
| P1 | Zwei Terminals / kein "ein Prozess" | Installer + systemd so dokumentieren, dass ein Befehl "Installation + Start"; langfristig Überlegung: Backend serviert gebautes Frontend |
| P2 | Kein First-Run-Wizard | UI-Komponente "Erste Schritte" und Erkennung "erster Start" (Phase 3) |
| P2 | Fehler ohne Reparatur | Konzeption Reparatur-Assistent + "Erfahrene Einstellungen" (Phase 3) |

---

## 6. MVP "One-Click Experience" (Definition)

**Minimum für "One-Click Experience":**

1. **Ein Befehl:** `curl -sSL https://get.pi-installer.io | bash` (oder aus Repo: `bash scripts/create_installer.sh`) – kein manuelles Git/Pip/Npm.
2. **Eine klare Abschlussmeldung:** "Öffnen Sie http://pi-installer.local" oder "http://\<IP\>:3001" – Nutzer weiß sofort, wo er die Oberfläche öffnet.
3. **Läuft nach Reboot:** systemd-Service, sodass nach Neustart PI-Installer automatisch startet, ohne erneutes manuelles Starten von Backend/Frontend.
4. **Fehlertoleranz:** Bei fehlendem Python/Node klare Meldung + optional Installationsanleitung oder Skript-Schritte (kein stiller Abbruch).

Alles darüber (SD-Card-Image, App-Store, First-Run-Wizard, Mehrsprachigkeit) erweitert die Experience, ist aber nicht Minimum für "One-Click".

---

*Nächster Schritt: Phase 1 umsetzen – `create_installer.sh` und `pi-installer.service`.*
