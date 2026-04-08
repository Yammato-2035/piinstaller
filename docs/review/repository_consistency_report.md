## Repository Consistency Report – Struktur & Dokumentation

_Stand: März 2026 – Fokus auf Konsistenz, nicht auf Funktionsumfang._

---

### 1. Root-Struktur (high-level)

**Ist-Stand (vereinfacht):**

- `backend/` – FastAPI-App, Module, Debug-System.
- `frontend/` – React/Tauri-Frontend, Build-Output unter `frontend/dist/`.
- `docs/` – Architektur-, User-, Developer-, Design- und Review-Dokumente.
- `scripts/` – Installations-/Start-/Service-Skripte.
- `config/` – z. B. `version.json`.
- `setuphelfer.service`, `setuphelfer-backend.service` – systemd-Vorlagen (Legacy: `pi-installer*.service`); siehe `docs/architecture/NAMING_AND_SERVICES.md`.
- `VERSION` – Versionsdatei laut bestehender Doku.
- `README.md` – Einstieg auf GitHub.

**Bewertung:**

- Struktur ist grundsätzlich klar und konsistent mit den letzten Doku-Anpassungen im `README.md`.
- `docs/` ist der zentrale Ort für alle Text-Dokumente; Root enthält nur die nötigsten Einstiegsdateien.

---

### 2. docs/-Struktur

**Hauptbereiche:**

- `docs/user/` – Nutzer-Doku (QUICKSTART, INSTALL, SSH_SETUP_TROUBLESHOOTING, WORKFLOW_QUICKSTART, PYTHON_SETUP, README_START, START_HERE.txt).
- `docs/architecture/` – Architektur-/Plan-/Feature-Dokumente (ARCHITECTURE, PLAN, FEATURES, TRANSFORMATIONSPLAN, UI_PLAN, UI_IMPROVEMENTS etc.).
- `docs/developer/` – Entwickler-Doku (BUILD_DEB, ERROR_RESOLUTION, VERSIONING, WORKFLOW_LAPTOP_PI, REMOTE_ENTWICKLUNG, REPOSITORY_ERSTELLEN, GITHUB_SETUP, README_remote_architecture, DEBIAN_TRIXIE etc.).
- `docs/design/` – Icon-/Grafik- und Terminologie-Doku (icon_usage, icon_list, graphics_system, asset_inventory, shared_icon_and_graphics_plan, terminology_cleanup).
- `docs/review/` – Audit-/Review-/Fix-Logs (SYSTEM_AUDIT_REPORT, ui_fix_log, final_ui_improvements, error_backlog_current_state, priority_a_fixes, priority_b_fixes, priority_c_backlog, final_error_priority_report etc.).
- `docs/testing/` – UI-Test-Planung und Logs.
- Diverse Spezialdokumente im Root von `docs/` (NVME, HDMI/Display, FREENOVE*, RADIO*, SD_CARD_IMAGE, PACKAGING, VIDEO_TUTORIALS, ANALYSE_HUERDEN, SICHERE_DEFAULTS, RESSOURCEN_MANAGEMENT, GET_PI_INSTALLER_IO etc.).

**Bewertung:**

- Die Unterstruktur ist logisch, aber historisch gewachsen.
- Mehrere Dateien in `architecture/` (z. B. PLAN, TRANSFORMATIONSPLAN, FINAL_SOLUTION) sind bewusst als **historische Planungsdokumente** zu verstehen (z. B. „ALTE VERSION“ in FINAL_SOLUTION.md).

---

### 3. Doppelte / überlappende Dokumentation

Beispiele (nicht vollständig, aber repräsentativ):

- **Installation / Einstieg**:
  - `README.md` – Kurzüberblick + Schnellstart.
  - `docs/user/INSTALL.md` – detaillierte Installationsanleitung.
  - `docs/user/QUICKSTART.md` – Schnellstart variantenreich beschrieben.
  - `docs/SYSTEM_INSTALLATION.md` – Systemweite Installation & FHS.
  - `docs/ANALYSE_HUERDEN.md` – Hürden, die u. a. Installation/Docs betreffen.
- **Architektur & Planung**:
  - `docs/architecture/ARCHITECTURE.md` – Kernarchitektur.
  - `docs/architecture/PLAN.md`, `TRANSFORMATIONSPLAN.md`, `FINAL_SOLUTION.md`, `PROJECT_SUMMARY.md`, `STARTED.md` – mehrere Wellen von Planungs-/Transformations-Dokumenten.
- **Remote-Companion / Smartphone**:
  - `docs/REMOTE_COMPANION.md`, `REMOTE_COMPANION_DEV.md`.
  - `docs/developer/README_remote_architecture.md`.

**Bewertung:**

- Teilweise gewollte Mehrstufigkeit (README → QUICKSTART → INSTALL → SYSTEM_INSTALLATION).
- Planungs- und Zielzustandsdokumente überlappen sich; einige sind explizit als „ALTE VERSION“ gekennzeichnet und sollten als historisch betrachtet werden.

---

### 4. Veraltete oder historisch markierte Dateien

Identifizierte Hinweise:

- `docs/architecture/FINAL_SOLUTION.md`:
  - Enthält explizit „ALTE VERSION (Python 3.13 inkompatibel)“ und „NEUE VERSION …“, ist also als zeitliche Momentaufnahme zu verstehen.
- `docs/developer/ERROR_RESOLUTION.md` und `docs/architecture/FINAL_SOLUTION.md` referenzieren `START_HERE.txt` als „Schnelle Referenz“ – die Datei liegt inzwischen unter `docs/user/START_HERE.txt`.

**Bewertung:**

- Diese Dokumente sind **nicht falsch**, aber teils historisch; es fehlt ein einheitlicher Hinweis („Historisch – nicht aktueller Stand“) an prominenter Stelle.
- Kein unmittelbarer Laufzeitfehler, aber Risiko für Fehlinterpretation bei neuen Entwicklern.

---

### 5. Nicht (oder nur indirekt) verlinkte Dokumente

Beispiele:

- Diverse Hardware-/Spezialdokumente (`FREENOVE_*`, `HDMI_*`, `NVME_*`, `RADIO_*`, `ASUS_ROG_FAN_CONTROL.md`, `PICTURE_FRAME_APP.md` usw.) sind nicht von README oder Kern-User-Doku direkt verlinkt.
- Einige Entwickler-Dokumente (`PACKAGING.md`, `GET_PI_INSTALLER_IO.md`, `CLONE_ARCHITECTURE.md`) sind überwiegend über interne Referenzen in anderen Docs erreichbar (nicht über README).

**Bewertung:**

- Aus Konsolidierungssicht wäre eine **kurze Index-Seite** in `docs/` sinnvoll, die diese Spezialthemen aufführt – wird in dieser Phase nur als Empfehlung festgehalten.
- Aktuell entsteht kein Funktionsfehler, aber die Entdeckbarkeit für neue Entwickler ist begrenzt.

---

### 6. Zusammenfassung Konsistenz

- **Konsistent**:
  - Root-Struktur (backend/frontend/docs/scripts/config/VERSION).
  - Zentrale Einstiegspfade: README → `docs/user/INSTALL.md`, `docs/user/QUICKSTART.md`, `docs/SYSTEM_INSTALLATION.md`.
  - Neuere Review-/Design-/Developer-Dokumente verweisen aufeinander (UX, UI-Modi, Beginner-First-Planung).

- **Bewusst inkonsistent / historisch**:
  - Mehrere Architektur-/Planungsdokumente mit teilweise widersprüchlichen Zielbildern – sind Stand heute als Archiv + Kontext zu lesen.
  - Versionierungs-Doku (`VERSION`-basiert) vs. zusätzliches `config/version.json`.

---

### 7. Empfehlungen (nur Dokumentation, keine Architekturänderung)

1. **Historische Docs kennzeichnen**  
   - In ausgewählten Dateien (z. B. `FINAL_SOLUTION.md`, ältere PLAN/TRANSFORMATIONS-Dokumente) einen klaren Hinweis „Historisch – nicht aktueller Stand“ am Anfang ergänzen.

2. **Index für Spezialthemen in docs/**  
   - Eine kurze Übersicht `docs/INDEX.md` oder ähnlich, die Hardware-/Spezialdokumente listet (FREENOVE, NVME, HDMI, RADIO etc.), damit diese Themen auffindbar bleiben.

3. **Versionierungsfrage separat klären**  
   - In einer eigenen, klar begrenzten Aufgabe entscheiden, wie `VERSION` und `config/version.json` zusammenspielen sollen; dann Doku anpassen.

---

### 8. Selbstprüfung Phase 5

- **Keine neuen Funktionen?**  
  - Ja. Es wurden ausschließlich Strukturen beschrieben und bewertet.

- **Keine Architekturänderungen?**  
  - Ja. Weder Code-Struktur noch Laufzeitverhalten wurden angerührt.

- **Nur Konsolidierung und Dokumentation?**  
  - Ja. Alle Maßnahmenvorschläge sind als spätere Aufgaben notiert, nicht umgesetzt.

- **Folgefehler betrachtet?**  
  - Ja. Mögliche Missverständnisse durch historische Docs und parallele Versionierungsquellen wurden explizit als Risiko aufgeführt.

