# UI-Test-Empfehlung

_Minimale Absicherung der kritischen UI-Flows – Vorschlag ohne bestehende Teststruktur_

---

## 1. Ausgangslage (Prüfung)

| Bereich | Befund |
|---------|--------|
| **Frontend** | Keine Vitest-, Playwright- oder Jest-Konfiguration |
| **Frontend package.json** | Keine Test-Skripte, kein @testing-library, kein vitest |
| **Testdateien** | Keine *.test.tsx, *.spec.tsx im Frontend |
| **Backend** | Python pytest in `backend/tests/` (API-Tests, keine UI) |
| **Vite** | Standard-Config ohne Test-Plugins |

**Fazit:** Es existiert keine UI-/Frontend-Teststruktur. Es wird ein Vorschlag dokumentiert statt eine komplette Testplattform neu aufzubauen.

---

## 2. Empfohlene Tools

### Option A: Vitest + React Testing Library (Komponententests)

| Tool | Zweck | Begründung |
|------|-------|------------|
| **Vitest** | Test-Runner | Mit Vite integriert, gleiche Config, schnelle Ausführung |
| **@testing-library/react** | Komponenten-Rendering | Fokus auf Nutzerverhalten, stabil gegenüber Refactorings |
| **jsdom** | DOM-Umgebung | Für Komponententests erforderlich |

**Aufwand:** ~30 Min Einrichtung (vitest.config.ts, Dependencies, ein beispielhafter Test).

### Option B: Playwright (E2E)

| Tool | Zweck | Begründung |
|------|-------|------------|
| **Playwright** | E2E-Browser-Tests | Echter Browser, Navigation, API-Mocks möglich |

**Aufwand:** Höher; Backend oder Mocks für API-Calls nötig.

### Empfehlung

**Start mit Option A (Vitest + RTL)** – schneller Einstieg, keine Laufzeitumgebung nötig, Komponententests decken Render-Fehler und fehlende Imports (z. B. Wifi) zuverlässig ab.

Playwright später ergänzen für 1–2 Smoke-Tests (App-Start, Navigation).

---

## 3. Die 5 wichtigsten Kernflows

Nach Priorität A (docs/review/final_ui_improvements.md) sollten zuerst diese Flows abgesichert werden:

| # | Flow | Risiko (ohne Test) | Testziel |
|---|------|-------------------|----------|
| 1 | **App startet** | Routing/Import-Fehler | Root render, keine Fehler |
| 2 | **Navigation** | Menü/Routing kaputt | Sidebar/Seiten erreichbar |
| 3 | **ControlCenter / WLAN** | Wifi-Import, Icon-Fehler | WLAN-Sektion rendert ohne Laufzeitfehler |
| 4 | **InstallationWizard** | Fortschritt fehlt | „Installation läuft“ + Fortschrittsbalken vorhanden |
| 5 | **RunningBackupModal / Clone** | Status-Feedback fehlt | Modal rendert mit Kern-Elementen |

---

## 4. Minimale Einführungsstrategie

### Phase 1: Grundlage (1 Tag)

1. Vitest + RTL installieren:
   ```bash
   cd frontend && npm i -D vitest @testing-library/react @testing-library/jest-dom jsdom
   ```

2. `vitest.config.ts` im Frontend-Root:
   ```typescript
   import { defineConfig } from 'vitest/config'
   import react from '@vitejs/plugin-react'
   export default defineConfig({
     plugins: [react()],
     test: { environment: 'jsdom', globals: true }
   })
   ```

3. `package.json` Script: `"test": "vitest run"`

4. Einen Pilot-Test schreiben, z. B. `InstallationWizard.test.tsx`:
   - Rendern ohne Fehler
   - Überschrift „Installationsassistent“ vorhanden
   - „Installation läuft“ bzw. Fortschrittsbalken vorhanden (wenn `installing` true)

### Phase 2: Kernflows (2–3 Tage)

5. Weitere Tests ergänzen:
   - `ControlCenter.test.tsx` – WLAN-Sektion rendert
   - `RunningBackupModal.test.tsx` – Modal rendert, Abbruch-Button vorhanden
   - `App.test.tsx` oder `app.navigation.test.tsx` – Root-Render, Sidebar sichtbar

### Phase 3: CI (optional)

6. In CI (GitHub Actions, GitLab CI) `npm run test` ausführen.

---

## 5. Konkrete Testdateien (nach Einrichtung)

| Datei | Inhalt (minimal) |
|-------|------------------|
| `InstallationWizard.test.tsx` | `render(<InstallationWizard />)`, `screen.getByText(/Installationsassistent/)`, `installing`-State: Fortschrittsbalken |
| `ControlCenter.test.tsx` | `render(<ControlCenter />)`, WLAN-Überschrift/Eingabe vorhanden, kein Crash |
| `RunningBackupModal.test.tsx` | `render(<RunningBackupModal ... />)`, Abbruch-Button, Statusbereich |
| `App.test.tsx` | `render(<App />)` mit Mock-Context, Sidebar/Navigation sichtbar |

---

## 6. Wichtige Einschränkungen

- **Keine Mocks für fetchApi**, außer wo nötig – sonst verbergen sie echte Fehler
- **Keine Snapshot-Tests** für ganze Seiten – zu fragil
- **Keine Pixel-Tests** – Layoutänderungen würden ständig Breaks verursachen
- **PlatformContext / UIModeContext** – für App-Tests ggf. Provider mocken

---

## 7. Nächster Schritt

Nach Freigabe: Phase 1 umsetzen (Vitest + RTL + Pilot-Test), dann schrittweise Phase 2.
