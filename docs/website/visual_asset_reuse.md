# Visuelle Asset-Wiederverwendung – setuphelfer.de

_Stand: März 2026 – Prüfung, welche Assets später auf setuphelfer.de genutzt werden können und welche Illustrationen sowohl für den Installer als auch für die Website geeignet sind._

---

## 1. Ziel

- Klarheit, **welche bestehenden und geplanten Grafiken** auf **setuphelfer.de** einsetzbar sind.
- **Doppelnutzung vermeiden:** Ein Asset – Installer + Doku + Website, wo sinnvoll.

---

## 2. Bereits vorhandene Assets – Website-Nutzung

### 2.1 Icons (`frontend/public/assets/icons/`)

| Kategorie | Eignung für setuphelfer.de | Einsatzideen |
|-----------|----------------------------|--------------|
| **navigation** | Sehr gut | Sektionen-Navigation (Dashboard, Setup, Backup, Apps, Hilfe, Erweiterte Funktionen), Menü, Footer |
| **status** | Sehr gut | Status-Boxen (Erfolg, Warnung, Fehler, Info), Checklisten, „System bereit“ |
| **devices** | Sehr gut | Erklärseiten zu Pi, Speicher (SD/NVMe/USB), Netzwerk, Display, Audio |
| **process** | Gut | „So funktioniert die Installation“ – Schritte (Suchen, Verbinden, Vorbereiten, Schreiben, Prüfen, Abschluss) |
| **diagnostic** | Gut | Doku zu Logs, Systemcheck, Debug, Fehlersuche |

**Fazit:** Alle 38 Icon-SVGs sind **websitefähig** (SVG, keine App-spezifischen Pfade). Gleiche Dateien können auf setuphelfer.de unter gleicher Pfadlogik (z. B. `/assets/icons/…`) eingebunden werden.

### 2.2 Screenshots (referenziert, aktuell nicht im Repo)

- In **Documentation.tsx** und **README** referenzierte Screenshots (z. B. `screenshot-dashboard.png`, `screenshot-wizard.png`) sind für **Dokumentation und Website** vorgesehen.
- Sobald die PNGs erstellt und abgelegt sind (z. B. `frontend/public/docs/screenshots/` oder zentral `assets/screenshots/`), können sie **unverändert** auf setuphelfer.de genutzt werden (Handbuch, Feature-Übersicht, Tutorials).

---

## 3. Geplante Illustrationen – Doppelnutzung Installer & Website

Aus `docs/design/missing_graphics.md` – folgende **fehlenden** Illustrationen sind für **beide** Kontexte (Installer + setuphelfer.de) geeignet:

### 3.1 Onboarding

| Grafik | Installer | setuphelfer.de |
|--------|-----------|----------------|
| welcome | First-Run-Wizard, Begrüßung | Landingpage Hero oder „Erste Schritte“ |
| system check | Schritt „System wird geprüft“ | Doku „Voraussetzungen prüfen“ |
| experience selection | Auswahl Einsteiger/Fortgeschritten/Experte | Erklärseite Zielgruppen |
| secure setup | Schritt Sicherheit | Sektion „Sichere Einrichtung“ |
| backup setup | Schritt Backup | Sektion „Backup einrichten“ |
| discover projects | Schritt Presets/Module | Sektion „Projekte entdecken“ |

### 3.2 Empty States

| Grafik | Installer | setuphelfer.de |
|--------|-----------|----------------|
| no projects | Leere Projektliste | Doku „Noch keine Presets“ |
| no backups | Keine Backups | Doku „Erstes Backup“ |
| no devices | Keine Geräte erkannt | Troubleshooting |
| no logs | Keine Log-Einträge | Doku Logs |

### 3.3 Statusgrafiken

| Grafik | Installer | setuphelfer.de |
|--------|-----------|----------------|
| system ok / system warning / system problem | Dashboard, Status-Screens | Status-Bereiche auf Doku-Seiten, FAQ |
| maintenance / check running | Wartungshinweise, laufende Prüfung | Doku „Updates“, „Systemcheck“ |

### 3.4 Community & Hilfe

| Grafik | Installer | setuphelfer.de |
|--------|-----------|----------------|
| community, share projects, help | Hilfe-Bereich, ggf. „Projekte teilen“ | Community-Sektion, Hilfe, Support |

### 3.5 Risk-System

| Grafik | Installer | setuphelfer.de |
|--------|-----------|----------------|
| safe, warning, critical | RiskLevelBadge, RiskWarningCard | Doku zu Sicherheitsstufen, Warnhinweise |

**Empfehlung:** Diese Illustrationen einmal **themen- und farbkonform** (siehe `asset_structure.md`, `graphics_system.md`) produzieren; dann in **Installer** (React/Tauri) und auf **setuphelfer.de** (statisch oder CMS) einbinden.

---

## 4. Installer-spezifisch vs. Website-spezifisch

- **Primär Installer, gut auf Website nutzbar:**  
  Projekt-Illustrationen (media server, NAS, smart home, music box, photo frame, retro gaming, learning environment, system monitor) – in der App für Presets/Module, auf der Website für Projekt-Übersichten und Feature-Beschreibungen.

- **Primär Website, optional Installer:**  
  Hero-Grafiken (z. B. „PI-Installer auf dem Pi“), große Section-Bilder für Landingpage – können bei Bedarf auch in der App (z. B. Doku-Tab) eingebunden werden.

- **Setup-Diagramme (setup flow, backup flow, install process, network, device detection):**  
  Für **beide** sinnvoll: Installer (Onboarding/Erklärung im Wizard), Website (Doku, „So funktioniert …“).

---

## 5. Technische Website-Kompatibilität

- **SVG:** Keine hardcodierten App-Pfade; Farben wo möglich über `currentColor` oder CSS-Variablen → direkt auf Website nutzbar.
- **PNG (Screenshots/Illustrationen):** Neutrale Pfade (z. B. `/assets/screenshots/`, `/assets/illustrations/`) wählen, die sowohl vom App-Build als auch vom Website-Build geladen werden können.
- **Ein Build, eine Quelle:** Idealerweise liegen alle geteilten Assets unter einer gemeinsamen Wurzel (z. B. `frontend/public/assets/` oder Repo-Root `assets/`), die sowohl Vite (App) als auch das Website-Tool (z. B. Static-Site-Generator) lesen kann.

---

## 6. Selbstprüfung Phase 5

- **Keine neuen Funktionen entwickelt?** – Ja.
- **Keine UI umgebaut?** – Ja.
- **Nur Dokumentation erstellt?** – Ja.
- **Assetstruktur websitefähig?** – Ja; Wiederverwendung und Doppelnutzung dokumentiert.
