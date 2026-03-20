# Aktueller Stand – Website setuphelfer.de

_Stand: März 2026 – Analyse des Repositories in Bezug auf Website, Branding, Design, Dokumentation und vorhandene Assets._

---

## 1. Bereits vorhandene Inhalte für die Website

- **Projekt-README (`README.md`):**
  - Umfassende Beschreibung des PI-Installers (Ziel, Kernfeatures, Systemanforderungen, Installationswege, Screenshots, Use Cases).
  - Klare Einordnung „Raspberry Pi Konfigurations-Assistent“, Fokus auf Sicherheit, Web-GUI, Einsteigerführung.
  - Diese Inhalte sind eine starke Basis für:
    - Startseite von setuphelfer.de (Hero, Vorteile, Features).
    - Download- und Installationsseiten (verschiedene Installationswege).
    - Dokumentationsbereiche (Links auf bestehende Docs).

- **Dokumentation unter `docs/` (Auswahl):**
  - Nutzer- und Entwicklerdokumente (`docs/user`, `docs/developer`, `docs/architecture`), z. B.:
    - `NETWORK_ACCESS.md`, `INSTALL.md`, `SYSTEM_INSTALLATION.md`
    - `ARCHITECTURE.md`, `FEATURES.md`, `VERSIONING.md`
  - Eignen sich direkt als Quelle für:
    - Dokumentationssektion der Website (Installationshilfe, Netzwerk, Backup, Diagnose).
    - Tutorials / vertiefende Seiten.

- **Security- und Review-Dokumente (`docs/review/security*`, `SECURITY.md`):**
  - Umfassende Sicherheits- und Hardening-Reports, Checklisten, Modulübersichten.
  - Können später in komprimierter, einsteigerfreundlicher Form in der Website-Dokumentation erscheinen (z. B. „Sichere Einrichtung“, „Risiken verstehen“).

- **Design- und Asset-Dokumentation (`docs/design/*`):**
  - `asset_structure.md`, `icon_inventory.md`, `illustration_inventory.md`, `missing_graphics.md`, `graphics_system.md` (indirekt referenziert).
  - Beschreiben bereits:
    - Gemeinsame Asset-Struktur für Installer, Doku, Website.
    - Farbsystem, Icon-System, geplante Illustrationen.
  - Diese Dokumente liefern die Grundlage für ein konsistentes Website-Designsystem.

- **Website-bezogene Dokumentation (`docs/website/visual_asset_reuse.md`, `asset_reuse_plan.md`):**
  - `visual_asset_reuse.md`: Listet auf, welche bestehenden Icons und geplanten Illustrationen für setuphelfer.de genutzt werden können.
  - `asset_reuse_plan.md`: Skizziert Einsatzideen für Assets (z. B. Status-Icons, Hero-Grafiken).
  - Zeigt: Website setuphelfer.de ist bereits als Teil der Gesamtstrategie gedacht; Fokus bisher auf Asset-Wiederverwendung, nicht auf kompletter Seitenstruktur.

---

## 2. Vorhandene Design-Assets und visuelle Sprache

- **Icons (bereit im Repo):**
  - Pfad: `frontend/public/assets/icons/` mit Unterordnern `navigation/`, `status/`, `devices/`, `process/`, `diagnostic/`.
  - Vollständig inventarisiert in `docs/design/icon_inventory.md` und zusammengefasst in `docs/review/visual_asset_status.md`.
  - In `docs/website/visual_asset_reuse.md` explizit als **websitefähig** markiert.
  - Stil: moderne, klare Line-Icons, an das PI-Installer UI angepasst.
  - Eignung:
    - Navigation & Sektionen auf setuphelfer.de (z. B. Bereiche „Projekte“, „Tutorials“, „Download“).
    - Statusanzeigen („System bereit“, „Warnung“, „Fehler“) im Dokumentationskontext.

- **Screenshots (referenziert, noch nicht physisch im Repo):**
  - In `README.md` und der Doku werden Screenshots wie `screenshot-dashboard.png`, `screenshot-wizard.png` referenziert.
  - `docs/review/visual_asset_status.md` und `docs/website/visual_asset_reuse.md` stellen klar:
    - Screenshots sind für Doku **und** Website vorgesehen.
    - Eine gemeinsame Ablage (z. B. `assets/screenshots/` oder `frontend/public/docs/screenshots/`) wird empfohlen.

- **Geplante Illustrationen/Diagramme (noch nicht umgesetzt):**
  - In `docs/design/missing_graphics.md` und `docs/review/visual_asset_status.md` dokumentiert:
    - Onboarding-Illustrationen (welcome, system check, experience selection, secure setup, backup setup, discover projects).
    - Projekt-Illustrationen (media server, NAS, smart home, etc.).
    - Setup-/Backup-/Netzwerk-Diagramme.
    - Risk-/Statusgrafiken, Community-/Hilfe-Illustrationen.
  - `docs/website/visual_asset_reuse.md` ordnet diese explizit der gemeinsamen Nutzung Installer + Website zu.

- **Farbsystem und Designprinzipien:**
  - In `docs/design/asset_structure.md` und weiteren Design-Dokumenten beschrieben:
    - Primärfarben (Sky-Blau), Statusfarben (OK, Warnung, Fehler, Info, Muted).
    - Regeln für SVG (currentColor, CSS-Variablen, ViewBox, Barrierefreiheit).
  - README beschreibt die GUI als:
    - Dark Mode mit Sky-Blue Accents.
    - Glasmorphism-Design.
    - Moderne, responsive Weboberfläche.
  - Diese Beschreibung ist die visuelle Grundlage, an die sich setuphelfer.de anlehnen soll.

---

## 3. Bereits vorhandene Strukturideen für setuphelfer.de

- **Direkte Website-Dokumente:**
  - `docs/website/visual_asset_reuse.md`: Fokus auf Wiederverwendung von Icons, Screenshots und künftigen Illustrationen für setuphelfer.de.
  - `docs/website/asset_reuse_plan.md`: Ergänzende Ideen, wie visuelle Assets auf der Website eingesetzt werden können (z. B. Hero-Bereich, Feature-Übersichten).

- **Indirekte Strukturideen aus Doku & Reports:**
  - Die vorhandene Dokumentation legt thematisch nahe:
    - Bereiche wie „Installationshilfe“, „Backup & Restore“, „Docker“, „Mailserver“, „Diagnose“, „Projekte/Presets“.
    - Einsteigerpfade („Weg 1: Sicher & manuell“, „Weg 2: One-Click“).
    - Sicherheits- und Risikoeinschätzung (Risk-System, Warnhinweise).
  - In `docs/review/visual_asset_status.md` und `asset_structure.md` wird explizit Bezug auf setuphelfer.de genommen:
    - Website als weiterer Konsument der Assets und Inhalte.
    - Fokus auf **gemeinsame Basis**, keine Sonderwelt nur für die Website.

---

## 4. Inhalte, die wiederverwendbar sind

- **Aus README und Kern-Dokumentation:**
  - Projektbeschreibung, Kernfeatures, Use Cases → Basis für:
    - Home/Startseite.
    - Übersichtsseiten „Was ist der PI-Installer?“.
  - Installationswege (manuell, One-Click, .deb, Docker) → Basis für:
    - Download-Seite.
    - Dokumentationsseiten „Installation“ und „Erste Schritte“.

- **Aus `docs/user/` und `docs/architecture/`:**
  - Netzwerkzugriff, Systeminstallation, Architekturübersichten → Basis für:
    - Dokumentationssektion (Installationshilfe, Netzwerk, Diagnose).
    - Tutorials/HowTos für Einsteiger („So erreichst du deinen Pi sicher“).

- **Aus Security- und Review-Dokumenten:**
  - Sicherheitskonzepte, Hardening-Checklisten, Risiko-Überlegungen → Basis für:
    - Einsteigerfreundliche Seiten zu „Sicherheit“ und „Risiko“.
    - Hinweise auf „nur im LAN nutzen / besser per VPN“.

- **Aus Design-/Asset-Dokumenten:**
  - Icon-System, Farbsystem, geplante Illustrationen → Basis für:
    - Wiederverwendbare Website-Komponenten (Feature-Karten, Status-Badges, Projektkarten).
    - Konsistente Darstellung von Projekten, Status, Risiko.

---

## 5. Offene Lücken / was fehlt

- **Keine vollständige Informationsarchitektur der Website:**
  - Top-Level-Navigation (Home, Projekte, Tutorials, Community, Download, Dokumentation, Über SetupHelfer) ist im Repo noch nicht als Struktur dokumentiert.
  - Nutzerpfade (Anfänger → Download, Hilfe → Doku/Community) sind noch nicht explizit beschrieben.

- **Kein definierter Seitenbaum für setuphelfer.de:**
  - Es existiert noch keine vollständige Liste der Seiten, Unterseiten und Templates für die Website.
  - Pflichtseiten wie Home, Projekte, Tutorials, Community, Download, Doku, Über-Seite sind noch nicht sauber als Seitenbaum ausgearbeitet.

- **Kein explizites Content-Modell für Website-Inhalte:**
  - Es fehlen strukturierte Modelle für:
    - Projekte.
    - Tutorials.
    - Dokumentationsseiten.
    - Community-/Forum-Bereiche.

- **Kein dediziertes visuelles Website-System (nur Asset-Grundlagen):**
  - Farbsystem, Icon-System und geplante Illustrationen sind dokumentiert.
  - Es fehlt jedoch:
    - Konkrete Definition von Website-Komponenten (Hero, Karten, Download-Boxen, Badges, Hinweisboxen, Tux-Komponenten).
    - Abgleich mit der UI des PI-Installers auf Seitenkomponenten-Ebene.

- **Keine WordPress-spezifische Zielarchitektur:**
  - Bisher keine Dokumentation zu:
    - Custom Post Types (Projekte, Tutorials, Doku, Nutzerprojekte).
    - Taxonomien (Schwierigkeit, Hardware, Thema, Risiko).
    - Menüstruktur, Rollen/Rechte, Forum-/Community-Struktur.

- **Keine technische Website-Struktur im Repo:**
  - Es existiert zwar `docs/website/…`, aber:
    - Kein eigener `website/`-Bereich mit `docs/`, `content/`, `assets/`, `templates/`.
    - Kein Mapping, wie Website-Doku und spätere Implementierung zusammenhängen.

- **Keine textuellen Wireframes / Seitenblaupausen:**
  - Es fehlen beschriebene Seitenlayouts (Sektionen, CTAs, Komponenten-Einsatz) für die Hauptseiten der Website.

- **Keine vorbereiteten Website-Inhalte:**
  - Es gibt noch keine separaten Content-Dateien (z. B. `website/content/*.md`) für:
    - Home.
    - Download.
    - Projekte-/Tutorial-Übersichten.
    - Community.
    - Über SetupHelfer.

- **Kein Umsetzungsplan speziell für setuphelfer.de:**
  - Es existieren zwar generelle Projektpläne/Reviews, aber kein dedizierter Implementierungsplan für die Website in Etappen.

---

## 6. Zusammenfassung & wiederverwendbare Design-Assets

- **Was ist bereits für die Website vorhanden?**
  - Sehr umfangreiche technische und nutzerorientierte Dokumentation zum PI-Installer.
  - Ein konsistentes Icon-System (38 Icons) und ein dokumentiertes Farbsystem.
  - Klare Planung für Illustrationen, Diagramme und Screenshots inklusive Wiederverwendung auf setuphelfer.de.
  - Erste websitebezogene Dokumente zur Asset-Wiederverwendung.

- **Welche Inhalte sind direkt wiederverwendbar?**
  - README-Texte (Projektbeschreibung, Features, Installationswege, Use Cases).
  - Nutzer- und Architekturdokumentation als Quelle für Doku-/Tutorialseiten.
  - Security-/Review-Dokumente für einsteigerfreundlich aufbereitete Sicherheitstexte.

- **Welche Design-Assets sind direkt wiederverwendbar?**
  - Alle Icons unter `frontend/public/assets/icons/` (Navigation, Status, Devices, Process, Diagnostic).
  - Künftige, zentral abgelegte Screenshots und Illustrationen gemäß `asset_structure.md` und `visual_asset_reuse.md`.

- **Welche offenen Lücken bestehen?**
  - Vollständige Informationsarchitektur und Seitenbaum von setuphelfer.de.
  - Content-Modelle für Projekte, Tutorials, Doku und Community.
  - Konkretes visuelles Website-Komponentensystem.
  - WordPress-Zielarchitektur (CPTs, Taxonomien, Menü, Rollen, Forum).
  - Klare Repository-Struktur für Website-Doku und -Implementierung.
  - Wireframes, Content-Entwürfe und Umsetzungsplan.

---

## 7. Selbstprüfung Phase 1

- **Keine neuen Funktionen erfunden?** – Ja, es wurde nur analysiert und dokumentiert.
-,**Fokus auf Analyse und Struktur?** – Ja, Inhalte und Assets wurden inventarisiert, Lücken klar benannt.
- **Vorhandene Projektlogik berücksichtigt?** – Ja, alle Aussagen stützen sich auf vorhandene README-/Docs-/Design-Dateien und das bestehende PI-Installer-Designsystem.

