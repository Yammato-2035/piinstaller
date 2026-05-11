# Domänengrenzen (Ist-Aufnahme – Stub)

**Status:** Rot – vorläufig, kein Code-Scan in diesem Schritt abgeschlossen.  
**Nächster Schritt:** Prompt `docs/cursor/PROMPT_05_MONOLITH_AUDIT.md` ausführen und diese Datei ersetzen/ergänzen.

## Ziel-Domänen (Soll-Katalog)

| Domäne | Beschreibung |
|--------|----------------|
| core.backup | Erstellung, Manifest, Archive |
| core.verify | Basic/Deep, Integrität, Hash |
| core.restore | Zielauswahl, Preview, Ausführung |
| core.storage | Erkennung, Mount-Infos, Medien |
| core.safety | Schreibschutz, interne Platten, Policies |
| core.inspect | Image/System-Inspect |
| core.rescue | Live/Rescue-Orchestrierung |
| core.evidence | Berichte, JSON-Exporte, Siegel |
| api.routes | HTTP API Oberfläche |
| ui | Frontend/Tauri |

## Bekannte Anker im Repo (ohne Vollständigkeit)

- Backend-Hauptlogik unter `backend/` mit Schwerpunkten `deploy/`, Recovery-/Backup-Tests unter `backend/tests/`.
- Rescue-/Runner-Pipeline: `backend/deploy/runner_rescue_*.py`.

## Gefahrzonen (vorläufig)

- Kopplung Deploy-Runner ↔ Backup/Restore (viele gemeinsame Test-Harnesses).
- Legacy-Bezeichner `pi-installer` / `PI_INSTALLER_DEV` neben Setuphelfer-Branding.

*Kein Refactoring ohne abgenommene Regression laut `docs/testing/REGRESSION_TEST_PLAN.md`.*
