# UI Test Log

_Dokumentation der UI-Teststruktur und -Abdeckung_

---

## Vorhandene Teststruktur

| Bereich | Status |
|---------|--------|
| **Frontend UI-Tests** | Keine |
| **Vitest** | Nicht vorhanden |
| **Playwright** | Nicht vorhanden |
| **React Testing Library** | Nicht vorhanden |
| **Jest** | Nicht konfiguriert (in PLAN.md/FEATURES.md als geplant erwähnt) |
| **Backend** | Python pytest in `backend/tests/` (API, keine UI) |

**Stand:** Es existiert keine automatisierte UI-Testabdeckung.

---

## Ergänzte Tests

*Keine – es wurde kein Test-Framework eingeführt. Bei fehlender Struktur ist nur eine Empfehlung erstellt worden (docs/testing/ui_test_recommendation.md).*

---

## Abgedeckte Kernflows

| Flow | Abgedeckt | Anmerkung |
|------|-----------|-----------|
| App startet | Nein | Kein Test |
| Hauptnavigation | Nein | Kein Test |
| ControlCenter / WLAN-Sektion | Nein | Kein Test |
| InstallationWizard | Nein | Kein Test |
| Fortschrittsanzeige | Nein | Kein Test |
| RunningBackupModal | Nein | Kein Test |
| Clone-/Statusbereich | Nein | Kein Test |

---

## Nicht abgedeckte Risiken

- **Laufzeitfehler** (z. B. fehlender Wifi-Import) werden erst bei manueller Nutzung sichtbar
- **Regression** nach Refactorings (z. B. Umbenennung, entfernte Imports)
- **Komponenten-Render** ohne funktionierende Prüfung

---

## Empfohlene nächste Tests

1. **Vitest + React Testing Library** einrichten (siehe ui_test_recommendation.md)
2. **Pilot-Test:** `InstallationWizard.test.tsx` – Rendering und Fortschrittsanzeige
3. **ControlCenter.test.tsx** – WLAN-Sektion ohne Crash
4. **RunningBackupModal.test.tsx** – Modal mit Kern-Elementen
5. **App.test.tsx** – Root-Render, Sidebar sichtbar

---

## Änderungshistorie

| Datum | Änderung |
|-------|----------|
| 2025-02 | Prüfung durchgeführt, keine UI-Teststruktur gefunden; ui_test_recommendation.md und ui_test_log.md erstellt |
