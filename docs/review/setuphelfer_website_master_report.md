# Master‑Report – setuphelfer.de

_Gesamtüberblick über Zielzustand, Struktur, Designsystem, WordPress‑Architektur und Community‑Konzept der Website setuphelfer.de._

---

## 1. Zielzustand der Website

setuphelfer.de ist die **öffentliche Plattform** rund um den PI‑Installer.  
Sie bündelt:

- eine **anfängerfreundliche Einführung** in den PI‑Installer,
- eine Übersicht über mögliche **Projekte/Szenarien**,
- strukturierte **Tutorials**,
- nachvollziehbare **Dokumentation**,
- eine **Community‑Struktur** für Fragen und Austausch.

Die Website selbst führt keine neuen Produktfunktionen ein, sondern macht das bestehende System sicht‑, versteh‑ und nutzbar.

---

## 2. Informationsarchitektur & Navigation

### 2.1 Informationsarchitektur

Definiert in `docs/website/information_architecture.md`:

- Top‑Level‑Bereiche:
  - Home.
  - Projekte.
  - Tutorials.
  - Community.
  - Download.
  - Dokumentation.
  - Über SetupHelfer.
- Jeder Bereich hat:
  - ein klares Ziel,
  - eine primäre Zielgruppe,
  - definierte Inhalte und CTAs,
  - eine klare Verbindung zum PI‑Installer.

### 2.2 Navigation & Nutzerpfade

Beschrieben in `navigation_structure.md` und `user_flows.md`:

- Hauptnavigation bildet alle Top‑Level‑Bereiche ab; auf Mobil als Burger‑Menü.
- Footer‑Navigation ergänzt Einstiege und rechtliche Links.
- Zentrale Nutzerpfade:
  1. Anfänger → Home → versteht Projekt → Download.
  2. Nutzer → Projekte → Projektdetail → Download/Tutorials.
  3. Nutzer → Hilfe → Tutorials/Doku → Community.
  4. Nutzer → Community → Forum (Hilfe & Support / Projekte teilen / Ankündigungen).

Die Architektur ist explizit auf **Einsteigerfreundlichkeit** und Klarheit ausgerichtet.

---

## 3. Seitenbaum & Content‑Modelle

### 3.1 Seitenbaum

`page_tree.md` beschreibt den vollständigen Seitenbaum:

- Kernseiten:
  - `/` (Home), `/projekte/`, `/tutorials/`, `/community/`, `/download/`, `/dokumentation/`, `/ueber/`.
- Unterseiten:
  - Projekt‑ und Tutorialkategorien, Detailseiten.
  - Doku‑Unterseiten (Installation, Backup, Docker, Mailserver, Diagnose, Allgemein).
- Künftige rechtliche Seiten:
  - Impressum, Datenschutz.

### 3.2 Content‑Modelle

`content_model.md` definiert strukturierte Modelle für:

- **Projekt** – Titel, Kurz/Langbeschreibung, Difficulty, Risk, Hardware, Kategorien, verknüpfte Tutorials/Doku.
- **Tutorial** – Ziel, Difficulty, Dauer, Voraussetzungen, Schritt‑Liste, Screenshots, Hinweise.
- **Dokumentationseintrag** – Themenbereich, Zusammenfassung, Langtext, Links zur Repo‑Doku.
- **Community‑Bereich** – Seitenebene für Community/Forum‑Einstieg.

Diese Modelle sind so angelegt, dass sie sich in WordPress‑CPTs und Felder (z. B. ACF) übertragen lassen.

---

## 4. Visuelles System & Komponenten

### 4.1 Visuelles System

In `visual_system.md` und `branding_usage.md`:

- Farbwelt:
  - Dunkle Basis + Sky‑Blue‑Akzente, Statusfarben (OK/Warning/Error/Info/Muted) in Anlehnung an die App.
- Typografie:
  - Moderne Sans‑Serif, klare Hierarchie.
- Bildsprache:
  - Wiederverwendung der bestehenden Icon‑Sets.
  - Geplante Illustrationen und Screenshots aus den Design‑Docs.
- Tux/Raspberry‑Pi‑Ästhetik:
  - Dezent und thematisch eingesetzt, kein Stilbruch.

### 4.2 Komponenten‑Patterns

In `component_patterns.md`:

- Hero‑Bereich.
- Feature‑Karten.
- Projekt‑, Tutorial‑, Community‑Karten.
- Download‑Boxen (Einsteiger/Alternativen).
- Status‑/Difficulty‑Badges.
- Hinweisboxen (Info/Warnung/Sicherheit).
- Tux‑Hinweis‑Komponenten.

Diese Komponenten sind bewusst einfach gehalten und orientieren sich an der bestehenden App‑UI.

---

## 5. WordPress‑Architektur & Plugins

### 5.1 WordPress‑Zielarchitektur

Beschrieben in `wordpress_architecture.md`:

- Custom Post Types:
  - Projekt.
  - Tutorial.
  - Dokumentationseintrag.
  - Optional: Nutzerprojekt.
- Taxonomien:
  - Schwierigkeit.
  - Hardware.
  - Thema.
  - Risiko.
- Menüstruktur:
  - Entspricht der definierten Navigation (Top‑Level + Untermenüs).
- Rollen/Rechte:
  - Admin, Redakteur, (optional) Autor; Moderation über bbPress.

### 5.2 Plugin‑Strategie

In `plugin_strategy.md`:

- Kern‑Plugins:
  - ACF (o. ä.) für Felder.
  - bbPress für Forum.
  - Schlanke Security‑ und Cache‑Plugins.
- Optional:
  - BuddyPress (nur bei Bedarf).
  - Einfaches SEO‑Plugin.
- Vermeidet:
  - Pagebuilder‑Zoo.
  - Mehrere Plugins für dieselbe Aufgabe.

Die Architektur bleibt damit schlank und wartbar.

---

## 6. Community‑Konzept

In `forum_and_community_plan.md` und `website/content/community.md`:

- Forum‑Basis: bbPress.
- Startstruktur:
  - Hilfe & Support.
  - Projekte teilen.
  - Ankündigungen (read‑only).
- Community‑Seite:
  - erklärt Zweck der Community,
  - verlinkt gezielt auf die Forenbereiche,
  - gibt Hinweise zu guten Fragen und Verhaltensregeln.
- Abgrenzung:
  - GitHub für Bugs/Features,
  - Forum für Nutzerfragen und Erfahrungsaustausch.

Die Community ist damit eng an die Website und den Installer angebunden, ohne eine überdimensionierte Social‑Plattform zu werden.

---

## 7. Technische Repo‑Struktur & Inhalte

### 7.1 Repository‑Mapping

`repository_mapping.md`:

- `docs/website/` enthält die komplette Website‑Konzeption.
- Ein zukünftiger `website/`‑Ordner ist als Implementierungsort vorgesehen:
  - `website/docs/`, `website/content/`, `website/assets/`, `website/templates/`.
- Gemeinsame Assets zwischen Installer und Website:
  - Icons, Screenshots, geplante Illustrationen/Diagramme.

### 7.2 Inhaltliche Vorbereitung

- `website/content/` enthält erste Textentwürfe für:
  - Home.
  - Download.
  - Projekte‑Übersicht.
  - Tutorials‑Übersicht.
  - Community‑Start.
  - Über SetupHelfer.

Diese Texte sind bewusst sachlich, einsteigerorientiert und lehnen sich an README/Doku an.

---

## 8. Umsetzungsplan

`implementation_plan.md` beschreibt Etappen:

1. **Struktur & Dokumentation** – (abgeschlossen) Konzept und Inhalte im Repo.
2. **WordPress‑Grundsystem** – saubere Installation, Basis‑Plugins.
3. **Theme / Designbasis** – Umsetzung der Designrichtlinien im Theme.
4. **Kernseiten** – Home, Download, Community, Doku‑Übersicht, Über.
5. **Projektbibliothek** – CPT Projekt + Archiv/Details.
6. **Tutorials** – CPT Tutorial + Archiv/Details.
7. **Dokumentation** – strukturierte Doku‑Einbindung.
8. **Community / Forum** – bbPress‑Struktur.
9. **Feinschliff / Inhalte / SEO** – glätten und nach tatsächlicher Nutzung ausbauen.

Der Plan priorisiert Nutzwert und Wartbarkeit und vermeidet „Big‑Bang“‑Umbauten.

---

## 9. Offene Punkte & spätere Ausbaustufen

- **Grafiken & Screenshots**
  - Viele benötigte Illustrationen sind konzeptionell beschrieben, müssen aber noch produziert werden.
  - Screenshots sollten konsistent erstellt und in einer gemeinsamen Ablage gepflegt werden.

- **Nutzerprojekte**
  - Optionaler CPT „Nutzerprojekt“ ist vorgesehen, wird aber erst nötig, wenn ausreichend Nachfrage entsteht.

- **Erweiterte Community‑Funktionen**
  - BuddyPress‑Integration oder zusätzliche Forenbereiche sind bewusst auf später verschoben.

- **Suche & Komfortfeatures**
  - Zentrale Suche über Doku/Tutorials/Projekte, Breadcrumbs, ggf. strukturierte Daten – alles sinnvolle, aber nachgelagerte Verbesserungen.

---

## 10. Bewusste Nicht‑Umsetzungen

- Kein eigener, parallel zum PI‑Installer laufender Funktionsumfang auf der Website (z. B. keine Web‑Konfiguration des Installers direkt über setuphelfer.de).
- Keine schwergewichtigen Pagebuilder‑Konstrukte, die die spätere Pflege erschweren.
- Kein unkontrollierter Einsatz von Plugins für „Kosmetik‑Features“.

Die Website bleibt damit eine **Informations‑ und Community‑Plattform**, kein zweites Backend.

---

## 11. Kritische Bewertung

- **Plattform‑Charakter**
  - Die Website deckt die Aufgaben ab, die für ein Ökosystem rund um den PI‑Installer sinnvoll sind: Einführung, Projekte, Tutorials, Doku, Community.
- **Anfängerpfad**
  - Mehrere Pfade führen Einsteiger sicher von Home/Download zu den ersten Schritten und Hilfsangeboten.
- **Verknüpfung Projekte–Tutorials–Community**
  - Projekte verweisen auf Tutorials und Doku, Tutorials wiederum auf Doku und Community; Doku verweist auf Tutorials und Community.  
  - So entsteht ein Netz statt isolierter Seiten.
- **Designkonsistenz**
  - Das visuelle System ist eng an den Installer gekoppelt; Icons, Screenshots und Farbwelt sind abgestimmt.

In Summe ist setuphelfer.de damit **als Plattform angelegt**, nicht als lose Sammlung von Seiten.

---

## 12. Abschließende Lagemeldung & Selbstprüfung

- **Was wurde erstellt?**
  - Vollständige Website‑Konzeption (Architektur, Seitenbaum, Content‑Modelle, Designsystem, WordPress‑Architektur, Community‑Plan) unter `docs/website/`.
  - Erste Inhaltsentwürfe für Kernseiten unter `website/content/`.

- **Was blieb bewusst offen?**
  - Konkrete Grafikproduktion.
  - Exakte technische Umsetzung im WordPress‑Theme (PHP/CSS) und Plugin‑Konfiguration.
  - Detailfragen zu künftigen Erweiterungen (Nutzerprojekte, erweiterte Suche, BuddyPress).

- **Regeln eingehalten?**
  - Keine neuen Produktfunktionen wurden erfunden.
  - Keine unnötigen technischen Experimente, Fokus auf Dokumentation und Struktur.
  - Alle Vorschläge sind WordPress‑tauglich und mit dem PI‑Installer visuell und inhaltlich verbunden.

