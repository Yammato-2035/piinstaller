# Repository-Mapping – setuphelfer.de

_Ziel: Klarheit darüber, wie Website-Dokumentation und spätere Implementierung im Repo organisiert sind und welche Assets gemeinsam mit dem PI-Installer genutzt werden._

---

## 1. Bestehende Struktur (Stand jetzt)

- **Root:**
  - `backend/` – PI-Installer Backend.
  - `frontend/` – PI-Installer Frontend (inkl. Icons und später Screenshots).
  - `docs/` – Architektur-, User-, Developer- und Review-Dokumentation.
  - `docs/website/` – Website-Konzept (Informationsarchitektur, Designsystem, WordPress-Architektur).

- **Website-spezifische Doku (bereits vorhanden):**
  - `docs/website/current_state_analysis.md`
  - `docs/website/information_architecture.md`
  - `docs/website/navigation_structure.md`
  - `docs/website/user_flows.md`
  - `docs/website/page_tree.md`
  - `docs/website/content_model.md`
  - `docs/website/project_template.md`
  - `docs/website/tutorial_template.md`
  - `docs/website/visual_system.md`
  - `docs/website/component_patterns.md`
  - `docs/website/branding_usage.md`
  - `docs/website/wordpress_architecture.md`
  - `docs/website/plugin_strategy.md`
  - `docs/website/forum_and_community_plan.md`

Diese Dateien bilden die konzeptionelle Grundlage der Website; es gibt aktuell noch keinen separaten `website/`-Implementierungsordner.

---

## 2. Geplante Website-Verzeichnisstruktur

Für die spätere Implementierung von setuphelfer.de wird ein eigener Bereich empfohlen:

```text
website/
  docs/        # Website-spezifische technische Umsetzung, Theme-Hinweise, WP-Setup-Notizen
  wireframes/  # (Option) Text-/Bild-Wireframes, falls später visuelle Skizzen hinzukommen
  content/     # Markdown-Entwürfe für Website-Texte (z. B. Home, Download, About)
  assets/      # Website-spezifische Assets (falls nicht direkt aus frontend/ genutzt)
  templates/   # HTML/Theme-Blueprints, Pseudo-Templates, evtl. PHP-Snippets
```

Hinweis:
- Diese Struktur ist **konzeptionell** beschrieben; physische Ordner können in einem späteren Schritt angelegt werden, wenn mit der konkreten Website-Implementierung begonnen wird.

---

## 3. Gemeinsame Assets Installer ↔ Website

### 3.1 Icons

- **Quelle im Repo:**
  - `frontend/public/assets/icons/`
    - `navigation/`
    - `status/`
    - `devices/`
    - `process/`
    - `diagnostic/`
- **Dokumentation:**
  - `docs/design/icon_inventory.md`
  - `docs/review/visual_asset_status.md`
  - `docs/website/visual_asset_reuse.md`
- **Nutzung:**
  - PI-Installer: über `AppIcon` und andere Komponenten.
  - Website: direkt als SVG-Assets (gleiche Pfade, z. B. `/assets/icons/navigation/icon_dashboard.svg`), insbesondere für Navigation und Karten.

### 3.2 Screenshots

- **Geplante Ablage:**
  - Entweder `frontend/public/docs/screenshots/` oder zentral `assets/screenshots/` (siehe `asset_structure.md` und `visual_asset_reuse.md`).
- **Nutzung:**
  - Installer-Dokumentation (z. B. README, Docs).
  - Website:
    - Home (GUI-Vorschau).
    - Download (Beispiele der Oberfläche).
    - Tutorials/Dokumentation (Schritt-Screenshots).

### 3.3 Illustrationen & Diagramme

- **Geplante Verzeichnisse (konzeptionell, siehe `asset_structure.md`):**
  - `assets/illustrations/`
  - `assets/diagrams/`
- **Nutzung:**
  - Sowohl im Installer (Onboarding, Empty States) als auch auf setuphelfer.de (Landingpage, Doku).

---

## 4. Website-spezifische Assets

Manche Grafiken werden primär für die Website erzeugt, können aber optional auch im Installer genutzt werden:

- **Beispiele:**
  - Hero-Illustrationen (z. B. „PI-Installer auf dem Raspberry Pi“).
  - Größere Header-Grafiken für Sektionen.

- **Empfohlene Ablage (konzeptionell):**
  - `website/assets/hero/`
  - `website/assets/sections/`

Diese Assets sollten das in `docs/design/asset_structure.md` und `docs/design/graphics_system.md` definierte Farbsystem und den Stil einhalten, damit die Option der Wiederverwendung im Installer offen bleibt.

---

## 5. Verbindung zwischen Doku und Implementierung

- **Dokumentationsquelle:**
  - Konzept- und Strukturdateien verbleiben in `docs/website/`.
- **Implementierungsquelle:**
  - Spätere technische Umsetzung (WordPress-Theme-Blueprints, HTML-/PHP-Snippets, CSS/Design-Notizen) wird in `website/` abgelegt.

Empfohlene Zuordnung:

- `docs/website/information_architecture.md` → Navigations- und Menüstruktur im Theme.
- `docs/website/page_tree.md` → Pages/CPT-Templates in `website/templates/`.
- `docs/website/content_model.md` → ACF-Feldgruppen-Definitionen, CPT-Registrierung.
- `docs/website/visual_system.md` + `component_patterns.md` + `branding_usage.md` → Design- und CSS-Richtlinien in `website/docs/` und Theme.

---

## 6. Auswirkungen auf bestehende Struktur

- **Keine bestehenden Ordner werden verändert oder gelöscht.**
- **Docs bleiben zentral in `docs/`**, inklusive `docs/website/`.
- `website/` wird als klar abgegrenzter Implementierungsbereich geplant, ohne das bestehende Backend/Frontend zu beeinflussen.

Dies stellt sicher:
- Saubere Trennung von:
  - App-Code (PI-Installer).
  - Website-Implementierung (setuphelfer.de).
  - Dokumentation/Design.

---

## 7. Selbstprüfung Phase 6 – Repository-Mapping

- **Keine unnötige Architekturänderung?**
  - Ja: Es werden nur klare Zuordnungen und eine optionale `website/`-Struktur beschrieben; bestehende Bereiche bleiben unangetastet.
- **Repo bleibt sauber?**
  - Ja: Website-Implementierung wird bewusst in einem eigenen, übersichtlichen Bereich gehalten.
- **Website-Bereich sinnvoll abgegrenzt?**
  - Ja: Doku in `docs/website/`, zukünftiger Code/Assets in `website/`, gemeinsame Assets klar beschrieben.

