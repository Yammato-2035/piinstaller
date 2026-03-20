# Content-Modell – setuphelfer.de

_Ziel: Einheitliche, WordPress-taugliche Struktur für Inhalte der Website. Fokus auf Projekte, Tutorials, Dokumentation und Community-Bereiche._

---

## 1. Content-Typ: Projekt

- **Zweck:**
  - Ein Projekt beschreibt ein konkretes Anwendungsszenario (z. B. Media-Server, NAS, Smart Home), das mit Hilfe des PI-Installers umgesetzt werden kann.

- **Felder (Konzept, später als CPT-Felder/ACF):**
  - `title` – Projekttitel (z. B. „Media-Server mit Raspberry Pi“).
  - `slug` – URL-Slug.
  - `short_description` – 1–2 Sätze, was das Projekt macht.
  - `long_description` – Ausführlichere Beschreibung (Ziele, Nutzen).
  - `difficulty` – Schwierigkeitsgrad (z. B. Anfänger, Fortgeschritten, Experte).
  - `risk_level` – Risiko-Einstufung (z. B. niedrig, mittel, hoch – abgeleitet aus dokumentiertem Risk-System).
  - `hardware_requirements` – Text/strukturierte Liste (Pi-Modell, Speicher, Zubehör).
  - `software_requirements` – Optional, falls besondere Voraussetzungen nötig sind.
  - `categories` – Projektkategorien (z. B. Server & Dienste, Smart Home, Multimedia, Lernen & Experimente).
  - `tags` – Freie Schlagwörter (z. B. „Home Assistant“, „Plex“, „NAS“).
  - `estimated_time` – grobe Zeitschätzung (optional).
  - `screenshots` – Referenzen auf vorhandene Screenshots/Illustrationen (Dateipfade, z. B. aus `assets/screenshots/`).
  - `related_tutorials` – Referenzen auf Tutorials (IDs/Slugs).
  - `related_docs` – Referenzen auf Doku-Seiten.
  - `callouts` – Wichtige Hinweise (z. B. Sicherheitswarnungen).

---

## 2. Content-Typ: Tutorial

- **Zweck:**
  - Schritt-für-Schritt-Anleitungen zu klar umrissenen Aufgaben, häufig in Verbindung mit Projekten oder Funktionsbereichen des PI-Installers.

- **Felder:**
  - `title` – Tutorialtitel.
  - `slug` – URL-Slug.
  - `short_description` – Kurzbeschreibung des Ziels.
  - `difficulty` – Schwierigkeitsgrad (Anfänger, Fortgeschritten, Experte).
  - `estimated_time` – grobe Dauer (z. B. 15–30 Minuten).
  - `categories` – Tutorialkategorien (Installation, Sicherheit & Backup, Projekte aufsetzen, Diagnose).
  - `tags` – Schlagwörter.
  - `prerequisites` – Voraussetzungen (z. B. „PI-Installer ist installiert“, „Projekt X ist angelegt“).
  - `required_hardware` – benötigte Hardware.
  - `steps` – Liste strukturierter Schritte (Überschrift + Text + optional Code/Screenshots/Hinweise).
  - `screenshots` – Bildreferenzen.
  - `related_projects` – Referenzen auf Projekte.
  - `related_docs` – Referenzen auf Doku-Seiten.
  - `callouts` – Hinweisboxen (Info/Warnung/Sicherheit).

---

## 3. Content-Typ: Dokumentationseintrag

- **Zweck:**
  - Technische Hintergrundinformationen zu Themen wie Installation, Backup, Docker, Mailserver, Diagnose, Netzwerk.

- **Felder:**
  - `title` – Titel des Doku-Eintrags.
  - `slug` – URL-Slug.
  - `section` – Hauptbereich (Installation, Backup, Docker, Mailserver, Diagnose, Allgemein).
  - `summary` – Kurzfassung, worum es geht.
  - `content` – Langtext mit Unterüberschriften, ggf. Codeblöcken.
  - `related_tutorials` – passende Tutorials.
  - `related_projects` – passende Projekte.
  - `risk_notes` – spezielle Risikohinweise (z. B. beim Öffnen von Ports, Mailserverbetrieb).
  - `links_to_repo_docs` – Links auf die entsprechenden Markdown-Dateien im Repository (Referenzen, keine Duplikate).

---

## 4. Content-Typ: Community-Bereich

- **Zweck:**
  - Beschreibt die Struktur der Community-Seiten und Forenbereiche (Konzept, nicht die einzelnen Beiträge).

- **Felder (für Seitenebene):**
  - `title` – z. B. „Community“, „Forum“.
  - `slug` – URL-Slug.
  - `description` – Worum es in diesem Bereich geht.
  - `sections` – Textblöcke (z. B. „Hilfe & Support“, „Projekte teilen“, „Ankündigungen“).
  - `rules_summary` – Kurzfassung der wichtigsten Regeln.
  - `links_forum_areas` – Ziel-URLs der Forenbereiche (bbPress-Foren).

> Einzelne Forenbeiträge/Threads werden später über bbPress verwaltet und gehören **nicht** in dieses Content-Modell.

---

## 5. Querschnitt: Labels und Taxonomien

Die folgenden Begriffe werden als Taxonomien bzw. wiederverwendbare Felder verstanden (Details in Phase 5 – WordPress-Architektur):

- **Schwierigkeit (Difficulty-Labels):**
  - Anfänger
  - Fortgeschritten
  - Experte

- **Risiko (Risk-Labels):**
  - niedrig
  - mittel
  - hoch  
  (semantisch angelehnt an das dokumentierte Risk-System und Statusfarben – keine neuen technischen Funktionen)

- **Hardware:**
  - z. B. „Raspberry Pi 4“, „Raspberry Pi 5“, „NVMe“, „USB-Speicher“, „DSI-Display“.

- **Thema:**
  - Installation, Sicherheit/Backup, Server & Dienste, Smart Home, Multimedia, Lernen, Diagnose.

---

## 6. Darstellung in Website-Komponenten (Kurzüberblick)

- **Projekt-Karten:**
  - Nutzen: `title`, `short_description`, `difficulty`, `risk_level`, `categories`, `hardware_requirements` (Kurzform), optional Icon/Illustration.

- **Tutorial-Karten:**
  - Nutzen: `title`, `short_description`, `difficulty`, `estimated_time`, `categories`.

- **Dokumentationsübersicht:**
  - Clustert `Dokumentationseinträge` nach `section` und zeigt `summary`.

- **Community-Startseite:**
  - Nutzt `Community-Bereich`-Daten, um die wichtigsten Einstiege als Karten/Links darzustellen.

---

## 7. Selbstprüfung Phase 3 – Content-Modell

- **Seitenbaum vollständig abbildbar?**
  - Ja: Projekte, Tutorials, Doku und Community-Bereiche lassen sich mit diesen Content-Typen strukturieren.
- **Konsistent mit Projektziel?**
  - Ja: Fokus bleibt auf PI-Installer, seinen Anwendungsfällen und Hilfestellungen; keine Fremdthemen.
- **Keine neue Produktlogik erfunden?**
  - Ja: Felder beschreiben Texte/Metadaten, keine neuen Funktionen im Installer. Risk- und Difficulty-Labels orientieren sich an bereits dokumentierten Konzepten.

