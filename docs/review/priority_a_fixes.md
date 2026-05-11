## Priorität A – Kritische Fehler & Brüche (Stand: März 2026)

Dieses Dokument listet bearbeitete und offene A‑Punkte.  
Nur minimale, zwingend notwendige Code‑Fixes; Schwerpunkt: Dokumentation und Korrektur zentraler Verweise.

---

### A‑01 – Wifi‑Import im Control Center (Laufzeitfehler)

- **Ausgangslage (Doku)**:
  - In `docs/review/ui_consistency_report.md`, `docs/review/final_ui_improvements.md` und `docs/review/project_improvement_summary.md` ist ein kritischer Fehler dokumentiert:
    - `ControlCenter.tsx` verwendet `<Wifi />` aus `lucide-react`, ohne `Wifi` zu importieren → Laufzeitfehler beim Rendern der WLAN‑Sektion.
- **Prüfung (aktueller Code)**:
  - Datei: `frontend/src/pages/ControlCenter.tsx`
  - Importzeile:
    - `import { Settings, Printer, Scan, Keyboard, Globe, Shield, Eye, Laptop, Mouse, Layout, Palette, Link2Off, Bluetooth, Fan, Headphones, Lightbulb, Wifi } from 'lucide-react'`
  - `Wifi` ist inzwischen korrekt importiert.
- **Bewertung**:
  - Der historische A‑Fehler ist im aktuellen Stand **bereits behoben**.
  - Kein weiterer Code‑Eingriff nötig.
- **Maßnahme**:
  - In späterer Runde Doku ggf. um Hinweis ergänzen, dass der Fix bestätigt wurde (z. B. in `ui_fix_log.md`).
- **Folgefehler**:
  - Keine unmittelbar sichtbar; weitere Icon‑Imports im `ControlCenter` wirken konsistent.

---

### A‑02 – README verweist auf verschobene Root‑Dokumente

- **Problem**:
  - `README.md` referenziert folgende Dateien im Projekt‑Root, die dort nicht mehr existieren, sondern nach `docs/…` verschoben wurden:
    - `INSTALL.md`, `ARCHITECTURE.md`, `FEATURES.md`, `SUGGESTIONS.md`, `VERSIONING.md`, `README_remote_architecture.md`.
  - Gleichzeitig beschreibt der Struktur‑Block eine Root‑Struktur mit diesen Dateien.
- **Risiko**:
  - Neue Nutzer und Entwickler landen beim Lesen des README auf 404‑Links bzw. falschen Erwartungen.
- **Status (Phase 1)**:
  - **Noch nicht korrigiert** – wird in `docs/review/documentation_breaks.md` im Detail beschrieben und anschließend im README minimal angepasst.
- **Empfohlene minimale Korrektur**:
  - Links im README auf die tatsächlichen Pfade unter `docs/user/`, `docs/architecture/` und `docs/developer/` umstellen.
  - Struktur‑Snippet so anpassen, dass nur reale Dateien genannt werden.
- **Codeänderung nötig?**:
  - **Nein.** Reine Dokumentationsänderungen.

---

### A‑03 – Versionierungsquellen (`VERSION` vs. `config/version.json`)

- **Problem (Doku‑Ist)**:
  - `docs/developer/VERSIONING.md`, `CHANGELOG.md`, `docs/developer/WORKFLOW_LAPTOP_PI.md` und andere beschreiben `VERSION` im Projektroot als „Quelle der Wahrheit“ für die Version.
  - Im aktuellen Repo existiert zusätzlich `config/version.json` als neue, strukturierte Quelle.
  - README verweist weiterhin auf `VERSION` + `VERSIONING.md`.
- **Risiko**:
  - Unklare Single‑Source‑of‑Truth für Versionen (Backend, Frontend, Tauri, Doku).
- **Status (Phase 1)**:
  - Noch kein Code‑Abgleich erfolgt (Backend/Frontend‑Nutzung von `config/version.json` vs. `VERSION` nicht geprüft).
  - Doku‑Bruch ist klar erkennbar und in `docs/review/documentation_breaks.md` erfasst.
- **Empfohlene minimale Korrektur**:
  - README und ggf. zentrale Doku so anpassen, dass klar ist, welches Format aktuell führend ist (ohne gleich die gesamte Versionierungslogik umzubauen).
- **Codeänderung nötig?**:
  - In dieser Phase **nein**; zunächst nur Doku bereinigen und Quellenlage beschreiben.

