## Terminology Cleanup – UI & Doku (Priorität B)

_Ziel: Bestehende Begriffs-Mischungen sichtbar machen und Korrekturen planen, ohne in dieser Phase breit UI-Texte umzubauen._

---

### 1. Referenz – UX Guidelines

Aus `docs/architecture/ux_guidelines.md` (vereinfacht):

- **Bevorzugte Begriffe** (deutsch):
  - „Installation“ (statt Setup/Deploy)
  - „Einstellungen“ (statt Settings, Config)
  - „Diagnose“ (statt Debug)
  - „Backend“ (als klarer technischer Begriff, wenn nötig)
  - „Status“ (statt State)
- Statusbegriffe:
  - „Bereit“, „Aktiv“, „Wird vorbereitet“, „Läuft“, „Abgeschlossen“, „Warnung“, „Fehler“

Diese Datei dient als **Soll-Zustand** für UI-Texte und Doku.

---

### 2. Bekannte Mischformen (Beispiele, kein Vollscan)

> Hinweis: Nur dokumentiert, keine Änderungen in dieser Phase, außer wo zwingend.

#### 2.1 README & Doku

- Begriffe wie:
  - „Setup“ und „Installation“ gemischt verwendet.
  - „Deploy“ in älteren Architektur-/Plan-Dokumenten.
  - „Debug“ für Nutzer-nahe Diagnosebereiche.
- Risiko:
  - Einsteiger können „Setup“ vs. „Installation“ vs. „Deploy“ nicht klar abgrenzen.

#### 2.2 UI-Komponenten (Auswahl)

Dateien mit gemischten Begriffen (per Grep gefunden; hier nur klassifiziert, nicht im Detail zitiert):

- `frontend/src/pages/InstallationWizard.tsx`
  - Spricht teils von „Installationsassistent“, teils von „Installation läuft“ – grundsätzlich konsistent, aber alte „Setup“-Begriffe könnten in Untertexten vorkommen.
- `frontend/src/pages/SecuritySetup.tsx`
  - Name `SecuritySetup` vs. UX-Richtlinie „Sicherheit“ / „Installation“.  
  - Im UI-Text vermutlich eine Mischung aus „Setup“, „Härtung“, „Konfiguration“.
- `frontend/src/pages/MailServerSetup.tsx`, `WebServerSetup.tsx`, `NASSetup.tsx`, `HomeAutomationSetup.tsx`
  - Seitennamen im Code enthalten „Setup“, während die UX-Richtlinie „Installation“ bzw. „Einrichten“ favorisiert.
- `frontend/src/pages/BackupRestore.tsx`
  - UI nutzt deutsche Begriffe („Backup erstellen“, „Wiederherstellen“), hier weitgehend konsistent.
- `frontend/src/pages/SettingsPage.tsx`
  - Mischung aus „Settings“, „Einstellungen“, „Diagnose“ je nach Tab/Label möglich.

> In dieser Phase wird **nur** festgehalten, dass es Diskrepanzen zwischen Dateinamen/Komponentennamen und den empfohlenen UI-Begriffen gibt. Eine Umbenennung im Code würde weitreichende Anpassungen erfordern und ist ausdrücklich **nicht** Ziel dieser Runde.

---

### 3. Priorisierte Bereinigungsfelder (nur Dokumentation)

1. **Seitennamen vs. UI-Titel**
   - `*Setup.tsx` vs. sichtbarer Titel „Mailserver einrichten“, „Webserver installieren“ etc.
   - Empfohlen später: Nur die **sichtbaren UI-Texte** (Titel, Buttons) an die Guidelines angleichen; Dateinamen können technisch bleiben.

2. **Diagnose vs. Debug**
   - Einige Doku-/UI-Stellen verwenden „Debug“ für Nutzer-nahe Bereiche (Logs, Tests).
   - Gemäß Guidelines sollte im UI „Diagnose“ verwendet werden; „Debug“ bleibt für Entwicklerdoku.

3. **Backend / Server / API**
   - README und Fehlermeldungen nennen teils „Backend“, teils „Server“, teils „API“.
   - Empfohlen: „Backend“ als Hauptbegriff, „Server“ optional ergänzen („Backend-Server“), „API“ primär in Entwicklerdoku.

---

### 4. Konkrete Korrekturvorschläge (für spätere Umsetzung)

> Nur als Plan notiert, **nicht** in dieser Phase umgesetzt.

1. **UI-Texte in kritischen Flows**:
   - Installationsassistent:
     - Konsistent „Installation starten“, „Installation läuft“, „Installation abgeschlossen“.
   - Sicherheitsseite:
     - „Sicherheit konfigurieren“ statt „Security Setup“ im sichtbaren UI-Text.

2. **Hauptnavigation**:
   - Sidebar-Titel:
     - „Diagnose“ statt „Debug“ für Diagnose-/Log-Bereiche.
   - Hilfetexte/Tooltips:
     - Backend-Fehler: „Bitte Backend starten (./scripts/start-backend.sh).“

3. **Dokumentation**:
   - In `docs/architecture/PLAN.md`, `TRANSFORMATIONSPLAN.md` und älteren Plan-Dokumenten:
     - Anmerkungen ergänzen, dass „Deploy“/„Setup“ historisch sind und in der UI durch „Installation“/„Einrichten“ ersetzt wurden.

---

### 5. Selbstprüfung Phase 2 (Terminologie)

- **Wurde funktional etwas geändert?**  
  - Nein. Es wurden nur vorkommende Begriffsmischungen gesammelt und spätere Korrekturen beschrieben.

- **Lag der Schwerpunkt auf Dokumentation?**  
  - Ja. Keine UI-Texte oder Komponenten wurden in dieser Phase angepasst.

- **Ist die spätere Bereinigung klar eingrenzbar?**  
  - Ja. Die Korrekturvorschläge fokussieren sich auf sichtbare Titel/Buttons/Doku, nicht auf Dateinamen oder API-Strukturen.

