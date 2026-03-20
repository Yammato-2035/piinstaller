# WordPress-Zielarchitektur – setuphelfer.de

_Ziel: Schlanke, realistische WordPress-Architektur für setuphelfer.de, klar ausgerichtet auf PI-Installer, Projekte, Tutorials, Dokumentation und Community – ohne Plugin-Overkill oder neue Produktlogik._

---

## 1. Grundsetup

- **System:**
  - WordPress als CMS.
  - Klassische Seitenstruktur (Pages) für:
    - Home, Community, Download, Dokumentation-Übersicht, Über SetupHelfer, rechtliche Seiten.
- **Dynamische Inhalte:**
  - Custom Post Types (CPTs) für:
    - Projekte.
    - Tutorials.
    - Dokumentationseinträge.
    - Optional: Nutzerprojekte.
  - Custom Taxonomies für:
    - Schwierigkeit.
    - Hardware.
    - Thema.
    - Risiko.
- **Felder:**
  - Erweiterung über ACF (oder vergleichbare Feld-Plugins) zur strukturierten Erfassung der im Content-Modell definierten Felder.

---

## 2. Custom Post Types (CPTs)

### 2.1 CPT: Projekt

- **Name/Slug:** `project` / `projekte`.
- **Einsatz:**
  - Alle Einträge für `/projekte/` und Projektdetailseiten.
- **Wichtige Felder (ACF o. Ä.):**
  - Kurzbeschreibung.
  - Hardware-Anforderungen.
  - Software-Anforderungen (optional).
  - Geschätzte Dauer.
  - Verknüpfte Tutorials.
  - Verknüpfte Doku-Einträge.
  - Risiko-Notizen.

### 2.2 CPT: Tutorial

- **Name/Slug:** `tutorial` / `tutorials`.
- **Einsatz:**
  - Alle Anleitungen in `/tutorials/` und Detailseiten.
- **Wichtige Felder:**
  - Kurzbeschreibung.
  - Geschätzte Dauer.
  - Voraussetzungen.
  - Benötigte Hardware.
  - Strukturierte Schritte (z. B. Repeater-Feld für Step-Titel + Text + Code + Hinweis-Typ).
  - Verknüpfte Projekte und Doku-Einträge.

### 2.3 CPT: Dokumentationseintrag

- **Name/Slug:** `doc_entry` / `doku`.
- **Einsatz:**
  - Detaillierte Doku-Seiten unter `/dokumentation/<thema>/`.
- **Wichtige Felder:**
  - Bereich (Installation, Backup, Docker, Mailserver, Diagnose, Allgemein).
  - Zusammenfassung.
  - Langtext.
  - Verknüpfte Tutorials und Projekte.
  - Links auf zugehörige Repository-Dokumente.

### 2.4 Optionaler CPT: Nutzerprojekt

- **Name/Slug:** `user_project`.
- **Einsatz (optional, später):**
  - Kuratierte, von Nutzern eingereichte Projekte (nicht Forenposts).
- **Hinweis:**
  - Erst einführen, wenn tatsächlicher Bedarf besteht; keine Pflicht für erste Ausbaustufe.

---

## 3. Taxonomien

### 3.1 Schwierigkeit (`difficulty`)

- **Typ:** Custom Taxonomy (hierarchiefrei).
- **Werte (Beispiele):**
  - Anfänger, Fortgeschritten, Experte.
- **Verknüpft mit:**
  - Projekte.
  - Tutorials.

### 3.2 Hardware (`hardware`)

- **Typ:** Custom Taxonomy.
- **Werte (Beispiele):**
  - Raspberry Pi 4, Raspberry Pi 5, SD-Karte, NVMe, USB-Speicher, DSI-Display.
- **Verknüpft mit:**
  - Projekte.
  - Tutorials.

### 3.3 Thema (`topic`)

- **Typ:** Custom Taxonomy.
- **Werte (Beispiele):**
  - Installation, Sicherheit & Backup, Server & Dienste, Smart Home, Multimedia, Lernen, Diagnose.
- **Verknüpft mit:**
  - Projekte.
  - Tutorials.
  - Doku-Einträge.

### 3.4 Risiko (`risk_level`)

- **Typ:** Custom Taxonomy.
- **Werte (Beispiele, angelehnt an Risk-System):**
  - niedrig, mittel, hoch.
- **Verknüpft mit:**
  - Projekte.
  - Tutorials.

---

## 4. Menüstruktur in WordPress

- Hauptmenü:
  - Home (Page).
  - Projekte (Archivseite CPT Projekte).
  - Tutorials (Archivseite CPT Tutorials).
  - Community (Page).
  - Download (Page).
  - Dokumentation (Page mit Untermenü).
  - Über SetupHelfer (Page).

- Footer-Menüs:
  - Einstieg (Home, Download, Erste Schritte).
  - Lernen (Projekte, Tutorials, Doku).
  - Community (Community, GitHub).
  - Rechtliches (Impressum, Datenschutz).

---

## 5. Rollen und Rechte (konzeptionell)

- **Rollen:**
  - Administrator:
    - Vollzugriff (System, Themes, Plugins).
  - Redakteur (Editor):
    - Verwalten von Projekten, Tutorials, Doku-Einträgen, Seiten.
  - Autor:
    - Eigene Tutorials/Beiträge verfassen (optional).
  - Community-Rollen:
    - Werden primär über bbPress/BuddyPress gesteuert (Moderatoren etc.).

- **Prinzip:**
  - Redakteure kümmern sich um Inhalte.
  - Technische Änderungen (Plugins, Theme) nur durch Admins.

---

## 6. Community-/Forum-Architektur (Überblick)

Details in `forum_and_community_plan.md`, hier nur Einbettung:

- **Forum:** bbPress.
- **Forenbereiche (Beispiele):**
  - Hilfe & Support.
  - Projekte teilen.
  - Ankündigungen (read-only).
- **Integration:**
  - Community-Seite (`/community/`) als Einstieg, verlinkt auf bbPress-Foren.
  - CTAs von Projekten/Tutorials/Doku führen in passende Forum-Bereiche.

---

## 7. Integration von ACF (oder ähnlichem)

- **Zweck:**
  - Abbilden der strukturierten Felder aus `content_model.md`.
- **Anwendung:**
  - Feldgruppen pro CPT (Projekt, Tutorial, Doku).
  - Repeater-Felder für Schrittlisten in Tutorials.
  - Relationen-Felder für `related_*`-Felder.

---

## 8. Selbstprüfung Phase 5 – WordPress-Architektur

- **Realistische WordPress-Struktur?**
  - Ja: Schlanke Anzahl an CPTs, klar definierte Taxonomien, ACF zur Feldverwaltung.
- **Nicht überladen?**
  - Ja: Nur die nötigsten Inhaltstypen und Taxonomien; Nutzerprojekte optional und später.
- **Community sinnvoll eingeordnet?**
  - Ja: Forum ist klar angebunden, aber in separatem Dokument detailliert; Website bleibt Content-zentriert.

