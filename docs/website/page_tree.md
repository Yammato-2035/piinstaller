# Seitenbaum – setuphelfer.de

_Ziel: Vollständiger, strukturierter Überblick über alle Seiten von setuphelfer.de. Basis für WordPress-Struktur, Navigation und Content-Planung._

---

## 1. Top-Level

- `/` – **Home**
- `/projekte/` – **Projekte – Übersicht**
- `/projekte/kategorie/<slug>/` – **Projektkategorie**
- `/projekte/<projekt-slug>/` – **Projektdetailseite**
- `/tutorials/` – **Tutorials – Übersicht**
- `/tutorials/kategorie/<slug>/` – **Tutorialkategorie**
- `/tutorials/<tutorial-slug>/` – **Tutorialdetailseite**
- `/community/` – **Community – Start**
- `/community/forum/` – **Forum-Einstieg** (später bbPress)
- `/download/` – **Download & erste Schritte**
- `/dokumentation/` – **Dokumentation – Übersicht**
- `/dokumentation/installation/` – **Installationshilfe**
- `/dokumentation/backup/` – **Backup & Restore**
- `/dokumentation/docker/` – **Docker**
- `/dokumentation/mailserver/` – **Mailserver**
- `/dokumentation/diagnose/` – **Diagnose & Logs**
- `/dokumentation/allgemein/` – **Allgemeine technische Hilfe**
- `/ueber/` – **Über SetupHelfer**

Zusätzlich (später, rechtlich):
- `/impressum/`
- `/datenschutz/`

---

## 2. HOME (`/`)

- **Sektionen:**
  - Hero
  - Projektvorstellung (PI-Installer)
  - Vorteile
  - Beispielprojekte
  - Community-Teaser
  - Download-CTA

- **Verlinkungen:**
  - CTAs zu `/download/`, `/projekte/`, `/tutorials/`, `/community/`, `/dokumentation/`, `/ueber/`.

---

## 3. PROJEKTE

### 3.1 Projektübersicht (`/projekte/`)

- Inhalte:
  - Einleitung „Was sind Projekte?“
  - Projektkarten (Liste aller veröffentlichten Projekte).
  - Filterleiste (Kategorie, Schwierigkeit, Hardware – UI-Ebene).

### 3.2 Projektkategorien (`/projekte/kategorie/<slug>/`)

- Beispiele:
  - `/projekte/kategorie/server-und-dienste/`
  - `/projekte/kategorie/smart-home/`
  - `/projekte/kategorie/multimedia/`
  - `/projekte/kategorie/lernen-und-experimente/`

- Inhalte:
  - Kurze Beschreibung der Kategorie.
  - Gefilterte Projektliste.

### 3.3 Projektdetailseite (`/projekte/<projekt-slug>/`)

- Inhalte:
  - Projektbeschreibung (Ziel, Nutzen).
  - Voraussetzungen (Hardware, OS, Erfahrungslevel).
  - Schwierigkeit & Risiko (Labels).
  - Schritt-Überblick (hochlevelig).
  - Verknüpfte Tutorials und Doku-Seiten.
  - CTAs: Download, Tutorials, Community.

---

## 4. TUTORIALS

### 4.1 Tutorials – Übersicht (`/tutorials/`)

- Inhalte:
  - Einleitung „Was sind Tutorials?“
  - Tutorialkarten (alle veröffentlichten Tutorials).
  - Filterleiste (Kategorie, Schwierigkeit, Thema).

### 4.2 Tutorialkategorien (`/tutorials/kategorie/<slug>/`)

- Beispiele:
  - `/tutorials/kategorie/installation/`
  - `/tutorials/kategorie/sicherheit-backup/`
  - `/tutorials/kategorie/projekte/`
  - `/tutorials/kategorie/diagnose/`

- Inhalte:
  - Beschreibung der Kategorie.
  - Gefilterte Tutorials.

### 4.3 Tutorialdetailseite (`/tutorials/<tutorial-slug>/`)

- Inhalte:
  - Klarer Titel und Kurzbeschreibung.
  - Metadaten (Schwierigkeit, Dauer, benötigte Hardware).
  - Schritt-für-Schritt-Anleitung (Sections/Steps).
  - Hinweisboxen (Hinweis/Warnung/Sicherheit).
  - Verknüpfungen:
    - Zu Projekten (falls relevant).
    - Zu Doku-Seiten (Hintergrund).
    - Zur Community (Fragen).

---

## 5. COMMUNITY

### 5.1 Community-Start (`/community/`)

- Inhalte:
  - Mission und Zweck der Community.
  - Einstiege:
    - Hilfe & Support.
    - Projekte teilen.
    - Ankündigungen lesen.
  - Verhaltensregeln / Netiquette (Kurzform, Link zur ausführlicheren Seite optional).

### 5.2 Forum-Einstieg (`/community/forum/`)

- Inhalte:
  - Übersicht über Forenbereiche (über bbPress realisiert).
  - Links zu:
    - „Hilfe & Support“.
    - „Projekte teilen“.
    - „Ankündigungen“.

---

## 6. DOWNLOAD (`/download/`)

- Sektionen:
  - Kurze Einleitung („Was lade ich hier herunter?“).
  - Empfohlener Installationsweg für Einsteiger (z. B. basierend auf „Weg 1: Sicher & manuell“ oder .deb, wie in README beschrieben).
  - Alternative Wege für Fortgeschrittene (Skript, Docker, etc.).
  - Systemanforderungen (aus README).
  - Screenshots (Oberfläche).
  - „Erste Schritte nach der Installation“ (Kurz-Checkliste).

---

## 7. DOKUMENTATION

### 7.1 Übersicht (`/dokumentation/`)

- Inhalte:
  - Einleitung „Wie ist die Dokumentation aufgebaut?“.
  - Karten/Links zu:
    - Installation.
    - Backup & Restore.
    - Docker.
    - Mailserver.
    - Diagnose & Logs.
    - Allgemeine technische Hilfe.

### 7.2 Installationshilfe (`/dokumentation/installation/`)

- Inhalte:
  - Zusammenfassung der vorhandenen Installations-Dokumente (INSTALL, SYSTEM_INSTALLATION etc.).
  - Klarer Bezug zu Download-Seite und Tutorials.

### 7.3 Backup & Restore (`/dokumentation/backup/`)

- Inhalte:
  - Hochlevel-Erklärung der Backup/Restore-Konzepte.
  - Links zu spezifischen Tutorials.

### 7.4 Docker (`/dokumentation/docker/`)

- Inhalte:
  - Überblick Docker-Nutzung für Test/Entwicklung (gemäß README).

### 7.5 Mailserver (`/dokumentation/mailserver/`)

- Inhalte:
  - Überblick Mailserver-Setup (basierend auf vorhandenen Dokumenten, kein neues Feature).

### 7.6 Diagnose & Logs (`/dokumentation/diagnose/`)

- Inhalte:
  - Logging, Debugging, Support-Bundle (basierend auf vorhandenen Debug-Dokumenten).

### 7.7 Allgemeine Hilfe (`/dokumentation/allgemein/`)

- Inhalte:
  - Allgemeine technische Hinweise, FAQ-ähnliche Inhalte, Netzwerk-Empfehlungen (LAN/VPN).

---

## 8. ÜBER SETUPHELFER (`/ueber/`)

- Sektionen:
  - Mission.
  - Philosophie.
  - Zielgruppen.
  - Roadmap (angelehnt an bestehende FEATURES-/Roadmap-Dokumente).
  - Mitmachen / Beitragen (Verweis auf CONTRIBUTING, GitHub).

---

## 9. Rechtliches (später)

- `/impressum/`
- `/datenschutz/`

---

## 10. Selbstprüfung Phase 3 – Seitenbaum

- **Seitenbaum vollständig?**
  - Ja: Alle in der Aufgabenstellung geforderten Bereiche und Unterseiten sind abgebildet.
- **Konsistent mit Projektziel?**
  - Ja: Fokus liegt auf PI-Installer, Projekten, Tutorials, Doku und Community; keine anderen Produkte.
- **Keine neue Produktlogik erfunden?**
  - Ja: Alle Seiten beschreiben Darstellung und Struktur, basierend auf bestehenden oder bereits geplanten Inhalten; keine neuen Features für den Installer selbst.

