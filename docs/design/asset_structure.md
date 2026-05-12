# Asset-Struktur – PI-Installer, Dokumentation, setuphelfer.de

_Stand: März 2026 – Einheitliche Struktur und Regeln für grafische Assets. Nur Dokumentation; keine neuen Ordner oder Dateien werden in dieser Phase angelegt._

---

## 1. Ziel

- **Gemeinsame Basis** für:
  - PI-Installer (App)
  - Dokumentation (docs, Screenshots)
  - Website setuphelfer.de
- **Eindeutige Benennung**, **SVG-Regeln** und **Farbnutzung** für spätere Grafikproduktion und Wiederverwendung.

---

## 2. Verzeichnisstruktur (Ziel)

```text
assets/
  icons/                    # Kleine UI-Symbole (Navigation, Status, Geräte, Prozess, Diagnose)
    navigation/
    status/
    devices/
    process/
    diagnostic/

  illustrations/            # Größere Illustrationen (Onboarding, Projekte, Empty States, …)
    onboarding/
    projects/
    empty_states/
    community/
    risk/

  diagrams/                 # Ablauf- und Prozessdiagramme (Setup, Backup, Netzwerk, Geräte)
    setup/
    backup/
    network/
    devices/
```

**Hinweis:** Im Repo ist aktuell nur `frontend/public/assets/icons/` mit Inhalt befüllt. `illustrations/` und `diagrams/` sind konzeptionell; Verzeichnisse können bei Bedarf bei der Grafikproduktion angelegt werden.

---

## 3. Dateibenennung

### 3.1 Icons

- **Schema:** `{kategorie}_{konzept}.svg` bzw. `icon_{konzept}.svg` in navigation.
- **Beispiele:** `status_ok.svg`, `status_warning.svg`, `icon_dashboard.svg`, `device_raspberrypi.svg`, `process_complete.svg`, `diagnose_logs.svg`.
- **Kleinbuchstaben, Unterstriche**, keine Leerzeichen, keine Umlaute in Dateinamen.
- **Ein Icon = eine Datei**; Varianten (z. B. gefüllt/outline) über Namenssuffix z. B. `_filled` vereinbar.

### 3.2 Illustrationen

- **Schema:** `illus_{bereich}_{name}.svg` (oder `.png` falls Raster gewünscht).
- **Beispiele:** `illus_onboarding_welcome.svg`, `illus_empty_no_projects.svg`, `illus_project_media_server.svg`, `illus_risk_safe.svg`.
- **Kleinbuchstaben, Unterstriche**; `bereich` = onboarding | projects | empty_states | community | risk.

### 3.3 Diagramme

- **Schema:** `diagram_{thema}_{name}.svg`.
- **Beispiele:** `diagram_setup_flow.svg`, `diagram_backup_flow.svg`, `diagram_network_connection.svg`, `diagram_devices_detection.svg`.

### 3.4 Screenshots (Dokumentation / Website)

- **Schema:** `screenshot-{seite}.png` (bereits in Doku verwendet).
- **Beispiele:** `screenshot-dashboard.png`, `screenshot-wizard.png`, `screenshot-backup.png`.
- Ablage: z. B. `frontend/public/docs/screenshots/` oder zentral `docs/screenshots/` / `assets/screenshots/` – je nach Build-/Website-Setup.

---

## 4. SVG-Regeln

- **Struktur:** Valides SVG, möglichst ohne eingebettete Rasterbilder; Pfade/Strokes bevorzugt.
- **Farben:**
  - **Nicht hart codieren**, wo später Theming nötig ist: `currentColor` oder CSS-Variablen nutzen.
  - Für **Status-Icons** kann die App per CSS-Filter einfärben (siehe `AppIcon.tsx` STATUS_FILTERS); SVG selbst idealerweise monochrom (z. B. schwarz/grau).
- **Größe:** ViewBox konsistent (z. B. 24×24 für Icons); keine festen width/height in px im SVG, damit Skalierung über CSS/width/height-Attribute bleibt.
- **Barrierefreiheit:** `<title>` und ggf. `<desc>` für Screenreader; `role="img"` und `aria-hidden` je nach Kontext.
- **Dateigröße:** SVG optimiert (z. B. ohne Editor-Metadaten); keine unnötigen Gruppen.

Details zu Stil (Linienstärke, Ecken, Komplexität) siehe `docs/design/graphics_system.md`.

---

## 5. Farbnutzung

- **Primär (App/Website):** Sky `#0284c7` / `#0ea5e9` für Akzente.
- **Status:** Grün (OK), Gelb/Orange (Warnung), Rot (Fehler), Blau (Info), Grau (deaktiviert) – siehe `graphics_system.md` und `AppIcon` STATUS_FILTERS.
- **Illustrationen/Diagramme:** Gleiche Palette nutzen, damit Wiederverwendung auf setuphelfer.de einheitlich wirkt. Wo möglich Farben über CSS/Variablen steuerbar halten.

---

## 6. Wiederverwendung für Website (setuphelfer.de)

- **Icons:** Dieselben SVG-Dateien aus `assets/icons/` können auf der Website (statisch oder per Build) eingebunden werden – gleiche Pfadlogik wie in der App (z. B. `/assets/icons/status/status_ok.svg`).
- **Illustrationen/Diagramme:** Sobald unter `assets/illustrations/` und `assets/diagrams/` vorhanden, können sie sowohl in der App (z. B. Empty States, Onboarding) als auch auf der Website (Landingpage, Doku, Hilfe) genutzt werden.
- **Screenshots:** Einmal erzeugte Screenshots (z. B. `screenshot-dashboard.png`) in einer gemeinsamen Ablage ermöglichen Nutzung in Installer-Doku und auf setuphelfer.de ohne Duplikate.
- **Keine App-spezifischen Pfade in SVG:** Relative Ressourcen oder absolute URLs vermeiden, die nur in der App funktionieren; dann bleiben Assets websitefähig.

---

## 7. Selbstprüfung Phase 4

- **Keine neuen Funktionen entwickelt?** – Ja.
- **Keine UI umgebaut?** – Ja.
- **Nur Dokumentation erstellt?** – Ja (Struktur und Regeln).
- **Assetstruktur websitefähig?** – Ja; gemeinsame Ordner und Benennung für Installer und setuphelfer.de beschrieben.
