# Navigationsstruktur – setuphelfer.de

_Ziel: Einfache, einsteigerfreundliche Navigation, die alle Hauptbereiche der Plattform sichtbar macht._

---

## 1. Top-Level-Menü

- **Home** → `/`
- **Projekte** → `/projekte/`
- **Tutorials** → `/tutorials/`
- **Community** → `/community/`
- **Download** → `/download/`
- **Dokumentation** → `/dokumentation/`
- **Über SetupHelfer** → `/ueber/`

Auf Mobilgeräten als Burger-Menü, visuell angelehnt an die Navigation des PI-Installers (Icons + Labels).

---

## 2. Wichtige Unterpunkte (konzeptionell)

- **Projekte**
  - „Alle Projekte“ → `/projekte/`
  - Projektkategorien (z. B. Server & Dienste, Smart Home, Multimedia, Lernen & Experimente) → `/projekte/kategorie/<slug>/`

- **Tutorials**
  - „Alle Tutorials“ → `/tutorials/`
  - Kategorien (Installation, Sicherheit & Backup, Projekte aufsetzen, Fehlersuche & Diagnose) → `/tutorials/kategorie/<slug>/`

- **Community**
  - Community-Start → `/community/`
  - Forum-Einstieg (später über bbPress) → `/community/forum/`

- **Dokumentation**
  - Übersicht → `/dokumentation/`
  - Themenseiten: Installation, Backup, Docker, Mailserver, Diagnose, Allgemeines → `/dokumentation/<thema>/`

---

## 3. Footer-Navigation

- **Einstieg**
  - Home
  - Download
  - Erste Schritte (Anker auf Download/Tutorial)

- **Lernen**
  - Projekte
  - Tutorials
  - Dokumentation

- **Community & Projekt**
  - Community
  - Über SetupHelfer
  - GitHub-Repository

- **Rechtliches** (später)
  - Impressum
  - Datenschutz

---

## 4. Visuelle Navigation

- Verwendung der bestehenden **Navigation-Icons** aus `frontend/public/assets/icons/navigation/` für das Hauptmenü.
- Wichtige Einstiege (z. B. „Download“, „Community“) werden zusätzlich als Buttons/CTAs hervorgehoben.

---

## 5. Selbstprüfung Phase 2 – Navigation

- **Anfängerfreundlich?** – Ja, klare, selbsterklärende Begriffe.
- **Architektur klar?** – Ja, logisch gruppierte Bereiche ohne Doppelungen.
- **Keine unnötigen Funktionen?** – Ja, nur Struktur und Benennung, keine neuen Produktfeatures.

# Navigationsstruktur – setuphelfer.de

_Ziel: Klar definierte, einsteigerfreundliche Navigation, die alle Kernbereiche (PI-Installer, Projekte, Tutorials, Community, Download, Dokumentation, Über) sichtbar macht und miteinander verbindet._

---

## 1. Top-Level-Navigation

- **Home** (`/`)
- **Projekte** (`/projekte/`)
- **Tutorials** (`/tutorials/`)
- **Community** (`/community/`)
- **Download** (`/download/`)
- **Dokumentation** (`/dokumentation/`)
- **Über SetupHelfer** (`/ueber/`)

Alle Punkte sind von jeder Seite aus erreichbar (Hauptmenü). Auf Mobilgeräten als Burger-Menü, visuell angelehnt an die Navigation des PI-Installers (Icons + Labels).

---

## 2. Hauptnavigation – Details

### 2.1 Home (`/`)

- **Sichtbar als:** „Home“ (optional nur Logo-Link auf Desktop).
- **Aufgabe in der Navigation:**
  - Rücksprung zur Startseite.
  - Für Einsteiger klarer Ausgangspunkt.

### 2.2 Projekte (`/projekte/`)

- **Unterpunkte (optional als Megamenü oder Untermenü):**
  - „Alle Projekte“ → `/projekte/`
  - „Server & Dienste“ → `/projekte/kategorie/server-und-dienste/`
  - „Smart Home“ → `/projekte/kategorie/smart-home/`
  - „Multimedia“ → `/projekte/kategorie/multimedia/`
  - „Lernen & Experimente“ → `/projekte/kategorie/lernen-und-experimente/`

### 2.3 Tutorials (`/tutorials/`)

- **Unterpunkte (optional):**
  - „Alle Tutorials“ → `/tutorials/`
  - „Installation & Erste Schritte“ → `/tutorials/kategorie/installation/`
  - „Sicherheit & Backup“ → `/tutorials/kategorie/sicherheit-backup/`
  - „Projekte aufsetzen“ → `/tutorials/kategorie/projekte/`
  - „Fehlersuche & Diagnose“ → `/tutorials/kategorie/diagnose/`

### 2.4 Community (`/community/`)

- **Unterpunkte (konzeptionell, später über Forum-Software abgebildet):**
  - „Community-Start“ → `/community/`
  - „Forum“ → `/community/forum/`
    - Innerhalb des Forums:
      - „Hilfe & Support“
      - „Projekte teilen“
      - „Ankündigungen“

### 2.5 Download (`/download/`)

- **Unterpunkte (optional als Anker auf derselben Seite):**
  - „Empfohlener Download für Einsteiger“
  - „Alternative Installationswege“
  - „Systemanforderungen“
  - „Erste Schritte nach Installation“

### 2.6 Dokumentation (`/dokumentation/`)

- **Unterpunkte (Hauptbereiche):**
  - „Übersicht“ → `/dokumentation/`
  - „Installation“ → `/dokumentation/installation/`
  - „Backup & Restore“ → `/dokumentation/backup/`
  - „Docker“ → `/dokumentation/docker/`
  - „Mailserver“ → `/dokumentation/mailserver/`
  - „Diagnose & Logs“ → `/dokumentation/diagnose/`
  - „Allgemeine Hilfe“ → `/dokumentation/allgemein/`

### 2.7 Über SetupHelfer (`/ueber/`)

- **Unterpunkte (optional als Anker):**
  - „Mission“
  - „Philosophie“
  - „Zielgruppen“
  - „Roadmap“
  - „Mitmachen / Beitragen“

---

## 3. Footer-Navigation

Der Footer wiederholt wichtige Einsteiger-Pfade und ergänzt rechtliche/organisatorische Links.

- **Bereich „Einstieg“**
  - Home
  - Download
  - Erste Schritte (Anker auf Download- oder Tutorialseite)

- **Bereich „Lernen & Projekte“**
  - Projekte
  - Tutorials
  - Dokumentation

- **Bereich „Community & Projekt“**
  - Community
  - Über SetupHelfer
  - GitHub-Repository

- **Bereich „Rechtliches“ (später zu ergänzen)**
  - Impressum
  - Datenschutz

---

## 4. Kontextnavigation innerhalb der Bereiche

### 4.1 Projekte

- **Seitliche oder horizontale Filterleiste:**
  - Filter nach:
    - Kategorie (Server, Smart Home, Multimedia, Lernen …).
    - Schwierigkeit (Anfänger, Fortgeschritten, Experte).
    - Hardware (z. B. Pi 4, Pi 5, externer Speicher).
  - Keine neuen technischen Funktionen, nur UI-Sicht auf spätere Filterlogik.

### 4.2 Tutorials

- **Filtermöglichkeiten ähnlich wie bei Projekten:**
  - Kategorie (Installation, Sicherheit, Projekte, Diagnose).
  - Schwierigkeit.

### 4.3 Dokumentation

- **Link-Blöcke nach Themen:**
  - Installation, Backup, Docker, Mailserver, Diagnose, Allgemeines.
  - Jede Doku-Seite bietet weiterführende Links zu Tutorials und Community.

---

## 5. Visuelle Navigationselemente (in Anlehnung an PI-Installer)

- **Icon-Einsatz in der Hauptnavigation:**
  - Nutzung vorhandener Icons aus `frontend/public/assets/icons/navigation/`:
    - z. B. `icon_dashboard.svg` für „Home“, `icon_installation.svg` für Download/Installation, `icon_help.svg` für Dokumentation/Community.
  - Konsistente Verwendung der Status-/Devices-/Process-Icons in Listen und Karten (z. B. Projekt- und Tutorialkarten).

- **Mobile Navigation:**
  - Burger-Menü mit denselben Einträgen wie Desktop.
  - Klar erkennbare CTAs für:
    - „Download“ (immer sichtbar).
    - „Community“ (für Hilfe sichtbar).

---

## 6. Zusammenfassung & Selbstprüfung Phase 2 – Navigation

- **Ist die Navigation anfängerfreundlich?**
  - Ja: Klare, sprechende Begriffe; wichtige Einstiege (Download, Tutorials, Community) sind direkt erreichbar.
- **Ist die Architektur klar?**
  - Ja: Top-Level und Unterpunkte sind thematisch sauber getrennt und konsistent mit der Informationsarchitektur.
- **Keine unnötigen Zusatzfunktionen eingebaut?**
  - Ja: Navigation beschreibt nur Struktur und Benennung, keine technischen Features oder komplexe Logik.

# Navigationsstruktur – setuphelfer.de

_Ziel: Klar definierte, einsteigerfreundliche Navigation, die alle Kernbereiche (PI-Installer, Projekte, Tutorials, Community, Download, Dokumentation, Über) sichtbar macht und miteinander verbindet._

---

## 1. Top-Level-Navigation

- **Home** (`/`)
- **Projekte** (`/projekte/`)
- **Tutorials** (`/tutorials/`)
- **Community** (`/community/`)
- **Download** (`/download/`)
- **Dokumentation** (`/dokumentation/`)
- **Über SetupHelfer** (`/ueber/`)

Alle Punkte sind von jeder Seite aus erreichbar (Hauptmenü). Auf Mobilgeräten als Burger-Menü, visuell angelehnt an die Navigation des PI-Installers (Icons + Labels).

---

## 2. Hauptnavigation – Details

### 2.1 Home (`/`)

- **Sichtbar als:** „Home“ (optional nur Logo-Link auf Desktop).
- **Aufgabe in der Navigation:**
  - Rücksprung zur Startseite.
  - Für Einsteiger klarer Ausgangspunkt.

### 2.2 Projekte (`/projekte/`)

- **Unterpunkte (optional als Megamenü oder Untermenü):**
  - „Alle Projekte“ → `/projekte/`
  - „Server & Dienste“ → `/projekte/kategorie/server-und-dienste/`
  - „Smart Home“ → `/projekte/kategorie/smart-home/`
  - „Multimedia“ → `/projekte/kategorie/multimedia/`
  - „Lernen & Experimente“ → `/projekte/kategorie/lernen-und-experimente/`

### 2.3 Tutorials (`/tutorials/`)

- **Unterpunkte (optional):**
  - „Alle Tutorials“ → `/tutorials/`
  - „Installation & Erste Schritte“ → `/tutorials/kategorie/installation/`
  - „Sicherheit & Backup“ → `/tutorials/kategorie/sicherheit-backup/`
  - „Projekte aufsetzen“ → `/tutorials/kategorie/projekte/`
  - „Fehlersuche & Diagnose“ → `/tutorials/kategorie/diagnose/`

### 2.4 Community (`/community/`)

- **Unterpunkte (konzeptionell, später über Forum-Software abgebildet):**
  - „Community-Start“ → `/community/`
  - „Forum“ → `/community/forum/`
    - Innerhalb des Forums:
      - „Hilfe & Support“
      - „Projekte teilen“
      - „Ankündigungen“

### 2.5 Download (`/download/`)

- **Unterpunkte (optional als Anker auf derselben Seite):**
  - „Empfohlener Download für Einsteiger“
  - „Alternative Installationswege“
  - „Systemanforderungen“
  - „Erste Schritte nach Installation“

### 2.6 Dokumentation (`/dokumentation/`)

- **Unterpunkte (Hauptbereiche):**
  - „Übersicht“ → `/dokumentation/`
  - „Installation“ → `/dokumentation/installation/`
  - „Backup & Restore“ → `/dokumentation/backup/`
  - „Docker“ → `/dokumentation/docker/`
  - „Mailserver“ → `/dokumentation/mailserver/`
  - „Diagnose & Logs“ → `/dokumentation/diagnose/`
  - „Allgemeine Hilfe“ → `/dokumentation/allgemein/`

### 2.7 Über SetupHelfer (`/ueber/`)

- **Unterpunkte (optional als Anker):**
  - „Mission“
  - „Philosophie“
  - „Zielgruppen“
  - „Roadmap“
  - „Mitmachen / Beitragen“

---

## 3. Footer-Navigation

Der Footer wiederholt wichtige Einsteiger-Pfade und ergänzt rechtliche/organisatorische Links.

- **Bereich „Einstieg“**
  - Home
  - Download
  - Erste Schritte (Anker auf Download- oder Tutorialseite)

- **Bereich „Lernen & Projekte“**
  - Projekte
  - Tutorials
  - Dokumentation

- **Bereich „Community & Projekt“**
  - Community
  - Über SetupHelfer
  - GitHub-Repository

- **Bereich „Rechtliches“ (später zu ergänzen)**
  - Impressum
  - Datenschutz

---

## 4. Kontextnavigation innerhalb der Bereiche

### 4.1 Projekte

- **Seitliche oder horizontale Filterleiste:**
  - Filter nach:
    - Kategorie (Server, Smart Home, Multimedia, Lernen …).
    - Schwierigkeit (Anfänger, Fortgeschritten, Experte).
    - Hardware (z. B. Pi 4, Pi 5, externer Speicher).
  - Keine neuen technischen Funktionen, nur UI-Sicht auf spätere Filterlogik.

### 4.2 Tutorials

- **Filtermöglichkeiten ähnlich wie bei Projekten:**
  - Kategorie (Installation, Sicherheit, Projekte, Diagnose).
  - Schwierigkeit.

### 4.3 Dokumentation

- **Link-Blöcke nach Themen:**
  - Installation, Backup, Docker, Mailserver, Diagnose, Allgemeines.
  - Jede Doku-Seite bietet weiterführende Links zu Tutorials und Community.

---

## 5. Visuelle Navigationselemente (in Anlehnung an PI-Installer)

- **Icon-Einsatz in der Hauptnavigation:**
  - Nutzung vorhandener Icons aus `frontend/public/assets/icons/navigation/`:
    - z. B. `icon_dashboard.svg` für „Home“, `icon_installation.svg` für Download/Installation, `icon_help.svg` für Dokumentation/Community.
  - Konsistente Verwendung der Status-/Devices-/Process-Icons in Listen und Karten (z. B. Projekt- und Tutorialkarten).

- **Mobile Navigation:**
  - Burger-Menü mit denselben Einträgen wie Desktop.
  - Klar erkennbare CTAs für:
    - „Download“ (immer sichtbar).
    - „Community“ (für Hilfe sichtbar).

---

## 6. Zusammenfassung & Selbstprüfung Phase 2 – Navigation

- **Ist die Navigation anfängerfreundlich?**
  - Ja: Klare, sprechende Begriffe; wichtige Einstiege (Download, Tutorials, Community) sind direkt erreichbar.
- **Ist die Architektur klar?**
  - Ja: Top-Level und Unterpunkte sind thematisch sauber getrennt und konsistent mit der Informationsarchitektur.
- **Keine unnötigen Zusatzfunktionen eingebaut?**
  - Ja: Navigation beschreibt nur Struktur und Benennung, keine technischen Features oder komplexe Logik.

