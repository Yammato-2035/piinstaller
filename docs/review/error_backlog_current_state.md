## Error & Inconsistency Backlog – Current State

_Stand: März 2026 – Quelle: Repository-Struktur, README, bestehende Docs/Reviews, UI-Code._

Priorisierung:

- **A** – Kritisch (Laufzeitfehler, irreführende zentrale Doku, Blocker für weitere Arbeiten)
- **B** – Wichtig (Konsistenz, UX, Terminologie, aber kein direkter Blocker)
- **C** – Nachrangig / kosmetisch

---

### A‑01 – README verweist auf verschobene Root‑Dokumente

- **Problem**: `README.md` verlinkt auf `INSTALL.md`, `ARCHITECTURE.md`, `FEATURES.md`, `SUGGESTIONS.md`, `VERSIONING.md`, `README_remote_architecture.md` im Projekt‑Root. Diese Dateien liegen inzwischen unter `docs/user/`, `docs/architecture/` bzw. `docs/developer/`.
- **Betroffener Bereich**: Einstieg über GitHub‑Seite, Root‑Doku.
- **Risiko**: Links führen ins Leere → neue Nutzer und Entwickler starten an der falschen Stelle oder halten das Projekt für unvollständig.
- **Empfohlene Maßnahme**: Links im `README.md` auf die neuen Pfade unter `docs/…` anpassen; Projektstruktur‑Block aktualisieren (Backend/Frontend/Docker‑Hinweise auf real existierende Dateien begrenzen).
- **Codeänderung nötig?**: **Nein**, reine Dokumentationskorrektur.
- **Mögliche Folgefehler**:
  - Doppelte oder widersprüchliche Einstiegspunkte (README vs. `docs/user/QUICKSTART.md`).
  - Veraltete Hinweise zu Versionierung (`VERSION`, `VERSIONING.md`) vs. neuer `config/version.json`.

---

### A‑02 – Projektstruktur im README weicht von realer Struktur ab

- **Problem**:
  - `README.md` beschreibt eine Struktur mit `Dockerfile`, `docker-compose.yml`, Root‑`INSTALL.md`, `ARCHITECTURE.md`, `FEATURES.md`, `SUGGESTIONS.md`, die so im Repo nicht mehr existiert bzw. an andere Orte verschoben wurde.
  - Systeminstallation (FHS `/opt/pi-installer/`, Scripts unter `scripts/`) ist im README nicht konsistent zu `docs/SYSTEM_INSTALLATION.md` und den aktuellen Startskripten (`scripts/start-*.sh`, `scripts/start-all.sh`).
- **Betroffener Bereich**: Einstieg für Entwickler und Administratoren.
- **Risiko**:
  - Falsche Annahmen über Container‑Support / Dockerfiles.
  - Falsche Startbefehle → Nutzer starten falsche oder nicht existierende Skripte.
- **Empfohlene Maßnahme**:
  - Projektstruktur‑Abschnitt auf _tatsächliche_ Verzeichnisse und Skripte reduzieren.
  - Auf `docs/SYSTEM_INSTALLATION.md` und `scripts/start-*.sh` verweisen statt nicht existenter Dateien.
- **Codeänderung nötig?**: **Nein**, Dokumentation.
- **Mögliche Folgefehler**:
  - Weitere README‑Stellen, die nicht zur FHS‑Installation passen (Services, Pfade, Version).

---

### A‑03 – Versionierungs‑Doku vs. `config/version.json`

- **Problem**:
  - Es existiert `config/version.json` als offensichtliche Single‑Source‑of‑Truth für die Version, gleichzeitig verweisen `README.md` und ältere Doku auf eine Datei `VERSION` und `VERSIONING.md` im Root.
  - Unklar, welche Quelle die „wahre“ Version für Backend/Frontend/Tauri ist.
- **Betroffener Bereich**: Release‑Prozess, Debugging, Benutzerinformationen zu Versionen.
- **Risiko**:
  - Falsche Versionsanzeige in UI/Logs.
  - Missverständnisse bei Bugreports („welche Version läuft wirklich?“).
- **Empfohlene Maßnahme**:
  - Dokumentarisch klarstellen, dass `config/version.json` die führende Quelle ist (falls dies confirmed ist).
  - Alte Hinweise auf `VERSION` in `README.md` korrigieren oder ergänzen (Übergangsabschnitt).
- **Codeänderung nötig?**: Voraussichtlich **nein** in Phase 0; erst prüfen, ob Backend/Frontend bereits `config/version.json` verwenden. Falls nicht konsistent, später minimal anpassen (Priorität A/B, separat dokumentieren).
- **Mögliche Folgefehler**:
  - Inkonsequente Versionen zwischen Systemd‑Service, Frontend‑About‑Dialog und Log‑Ausgaben.

---

### A‑04 – Kritischer Wifi‑Import‑Fehler im Control Center (historisch)

- **Problem**:
  - Doku (`docs/review/ui_consistency_report.md`, `docs/review/final_ui_improvements.md`, `docs/review/project_improvement_summary.md`) beschreibt einen **kritischen Laufzeitfehler**: `ControlCenter.tsx` verwendet `<Wifi />` aus `lucide-react`, ohne es zu importieren.
  - In den Review‑Docs ist dieser Punkt als „erledigt“ markiert (Import ergänzt).
- **Betroffener Bereich**: Frontend – `ControlCenter`‑Seite, WLAN‑Sektion.
- **Risiko**:
  - Falls der Fix nicht (oder nicht überall) umgesetzt ist, crasht die WLAN‑Sektion bei Rendern.
- **Empfohlene Maßnahme**:
  - Quellcode von `ControlCenter` (TSX‑Datei) gezielt prüfen, ob `Wifi` korrekt importiert wird.
  - Ergebnis in Priorität‑A‑Dokument (`docs/review/priority_a_fixes.md`) festhalten.
- **Codeänderung nötig?**:
  - **Nur**, falls `Wifi` immer noch fehlt; dann minimalen Import ergänzen.
  - In Phase 0: nur als offener Punkt dokumentiert; Umsetzung in Phase 1.
- **Mögliche Folgefehler**:
  - Weitere Icon‑Imports im `ControlCenter` könnten ähnliche Probleme haben (andere Lucide‑Icons, gemischte Systeme).

---

### A‑05 – Dokumentierte kritische Pfade ohne Abgleich mit aktuellem Code

- **Problem**:
  - `docs/SYSTEM_AUDIT_REPORT.md`, `docs/architecture/init_flow.md`, `docs/PATHS_NVME.md`, `docs/development/anti_regression_summary.md` markieren kritische Bereiche (u. a. `backend/app.py`, `backend/debug/support_bundle.py`, NVMe‑Clone, Boot‑Pfad), ohne dass im Backlog ein aktueller Abgleich mit dem Codezustand dokumentiert ist.
  - Beispiel: Hinweis auf möglichen Laufzeitfehler in `backend/debug/support_bundle.py` (`_redact_text_line_by_line()` nutzt `compile_patterns()` ohne erkennbaren Import).
- **Betroffener Bereich**: Backend – Debug/Support‑Bundle, Systemstart‑Flow, NVMe‑Boot.
- **Risiko**:
  - Fehler in selten genutzten, aber sicherheitsrelevanten Pfaden (Support‑Bundle im Fehlerfall) werden erst im Ernstfall sichtbar.
- **Empfohlene Maßnahme**:
  - Phase‑weise Prüfung in Priorität A (nur die klar als kritisch markierten Pfade; keine breite Refaktorierung).
  - Zuerst dokumentieren, _wo_ Code vs. Doku möglicherweise auseinanderlaufen (z. B. Support‑Bundle‑Imports).
- **Codeänderung nötig?**:
  - In Phase 0: **nein**, nur Backlog‑Eintrag.
  - Spätere minimal nötige Fixes in Phase 1 falls Reproduktion möglich.
- **Mögliche Folgefehler**:
  - Weitere unentdeckte Import‑/Pfadfehler im Debug‑/Support‑Bundle‑System.

---

### B‑01 – Gemischtes Icon‑System (dist‑SVGs vs. React‑Icons)

- **Problem**:
  - Es existiert ein umfangreiches SVG‑Icons‑Set unter `frontend/dist/assets/icons/...` (Status, Process, Devices, Navigation, Diagnostic).
  - Gleichzeitig nutzt der React‑Code `AppIcon`, Lucide‑Icons (`lucide-react`) und eigene Komponenten (`RiskLevelBadge`, `RiskWarningCard`).
  - `docs/design/icon_usage.md`, `icon_list.md`, `graphics_system.md` dokumentieren ein Icon‑System, das teilweise von der tatsächlichen Nutzung im Frontend abweicht (z. B. einige geplante Icons nicht oder anders verwendet).
- **Betroffener Bereich**: Frontend UI, Design‑System, spätere Website‑Assets.
- **Risiko**:
  - Uneinheitliche Darstellung (z. B. unterschiedliche Symbole für denselben Status).
  - Erschwerte Wiederverwendung für eine spätere Website, da nicht klar ist, welche Assets „offiziell“ sind.
- **Empfohlene Maßnahme**:
  - Inventar und Zuordnung in Phase 2 (`docs/design/asset_inventory.md`, `shared_icon_and_graphics_plan.md`) präzisieren.
  - Im Code nur minimale Korrekturen dort, wo Inkonsistenzen direkt Fehler/Verwirrung auslösen.
- **Codeänderung nötig?**: **Nein** in Phase 0; später gezielt bei konkreten B‑Fehlern.
- **Mögliche Folgefehler**:
  - Weitere gemischte Icon‑Verwendung (Lucide vs. AppIcon vs. SVGs) ohne klare Linie.

---

### B‑02 – Terminologie‑Mischung in Doku und UI

- **Problem**:
  - `docs/architecture/ux_guidelines.md` definiert klare Begriffe (z. B. „Installation“, „Einstellungen“, „Diagnose“, „Backend“).
  - README, einige Seiten und ältere Doku verwenden dennoch gemischte Begriffe („Setup“, „Deploy“, „Debug“, „Server“, „API“) ohne konsequente Anpassung.
- **Betroffener Bereich**: Nutzer‑Doku, UI‑Texte, Fehlermeldungen.
- **Risiko**:
  - Einsteiger verstehen nicht, dass „Backend starten“ und „Server starten“ dasselbe meinen.
  - Entwickler orientieren sich an veralteten Begriffen aus Reviews.
- **Empfohlene Maßnahme**:
  - In Phase 2 systematische Erfassung in `docs/design/terminology_cleanup.md`.
  - README und zentrale Hilfetexte schrittweise an die Guidelines anpassen (minimale Textänderungen).
- **Codeänderung nötig?**:
  - Teilweise UI‑Text‑Anpassungen (kein Funktionsverhalten), daher als Doku‑nahe Änderungen einzuordnen.
- **Mögliche Folgefehler**:
  - Unterschiedliche Begriffe in Bugreports vs. Code/Docs erschweren Kommunikation.

---

### B‑03 – Beginner‑First‑Architektur vs. ältere Doku

- **Problem**:
  - Es existieren neuere Dokumente (`docs/review/beginner_restructure_plan.md`, `docs/architecture/ui_modes.md`, `docs/architecture/foundation_vs_advanced_map.md`), die Beginner‑First‑Ideen beschreiben.
  - Ältere Doku (z. B. `docs/architecture/PLAN.md`, `TRANSFORMATIONSPLAN.md`, Teile des README) beschreibt noch die modul‑zentrierte Sicht (viele Seiten, alle gleich sichtbar).
- **Betroffener Bereich**: Konzept‑Doku, Erwartungsmanagement.
- **Risiko**:
  - Verwirrung, welche UI‑Architektur aktuell gilt.
  - Entwickler können versehentlich alte Navigation wiederbeleben.
- **Empfohlene Maßnahme**:
  - In Phase 1/2 klar trennen: „Altplan (historisch)“ vs. „aktueller Plan“ und ggf. kurze Hinweise in den alten Dokumenten ergänzen (ohne Inhalt zu löschen).
- **Codeänderung nötig?**: **Nein** in Phase 0.
- **Mögliche Folgefehler**:
  - Falsche Ableitungen bei künftigen Refactorings (z. B. Sidebar).

---

### C‑01 – README Marketing‑/Performance‑Angaben ohne Abgleich

- **Problem**:
  - README enthält harte Aussagen wie „Frontend Build ~150KB“, „API Response <100ms“, „Production Ready“, „Support bis Januar 2027“, ohne dass ein Abgleich mit aktuellem Stand dokumentiert ist.
- **Betroffener Bereich**: Erwartungsmanagement, Außendarstellung.
- **Risiko**:
  - Gering, eher reputationsbezogen; keine direkten Laufzeitfehler.
- **Empfohlene Maßnahme**:
  - In Phase 3 als kosmetische Punkte dokumentieren; optional relativierende Formulierungen einführen.
- **Codeänderung nötig?**: **Nein**.
- **Mögliche Folgefehler**:
  - Mismatch zu späteren Benchmarks oder Audit‑Ergebnissen.

---

## Zusammenfassung Phase 0

- **Erkannte Schwerpunkte**:
  - Zentrale Doku‑Brüche im `README` (Pfade, Struktur, Versionierung).
  - Historisch dokumentierter kritischer Wifi‑Import‑Fehler im `ControlCenter` (Status im Code noch zu verifizieren).
  - Kritische Backend‑Pfade (Support‑Bundle, Init‑Flow, NVMe‑Clone) sind in Audit‑Doku markiert, ohne jüngste Bestätigung.
  - Breiter Mix aus Icon‑/Terminologiesystemen, bereits in Design‑Docs beschrieben.

- **Priorität A (aktuell sichtbar)**:
  - A‑01 / A‑02: Falsche/fehlleitende Verweise im `README.md`.
  - A‑03: Unklare Versionierungsquelle (`VERSION` vs. `config/version.json`).
  - A‑04 / A‑05: Historisch kritischer Wifi‑Import im ControlCenter + kritische Debug-/Support‑Bundle‑Pfade.

- **Neue Folgefehler / Folgefragen**:
  - Ob der Wifi‑Import‑Fehler im aktuellen `ControlCenter`‑Code wirklich behoben ist.
  - Ob `config/version.json` in Backend/Frontend/Tauri konsistent genutzt wird oder nur „bereitliegt“.
  - Ob Support‑Bundle‑Imports tatsächlich zu Laufzeitfehlern führen können (noch nicht geprüft).

---

## Selbstprüfung Phase 0

- **Wurden neue Features geplant?**  
  - **Nein.** Alle Punkte sind als Backlog/Fehlerliste dokumentiert, ohne neue Funktionen zu konzipieren.

- **Liegt der Fokus auf Dokumentation?**  
  - **Ja.** Es wurde ausschließlich eine Review‑Doku (`docs/review/error_backlog_current_state.md`) angelegt, keine funktionalen Änderungen.

- **Wurden nur bestehende Probleme betrachtet?**  
  - **Ja.** Grundlage sind vorhandene Dateien, Reviews, Audit‑Berichte und die sichtbare Projektstruktur; es wurden keine hypothetischen neuen Problemfelder erfunden.

