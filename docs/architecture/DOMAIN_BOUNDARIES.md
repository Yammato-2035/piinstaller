# Domänengrenzen (Verweis)

**Status:** Ersetzt durch Monolith-Audit 2026-05-20.  
**Verbindliche Dokumente:**

- [`MONOLITH_BOUNDARY_AUDIT_2026-05-20.md`](MONOLITH_BOUNDARY_AUDIT_2026-05-20.md) — Ist, Duplikate, Risiken  
- [`MODULE_BOUNDARIES_TARGET_2026-05-20.md`](MODULE_BOUNDARIES_TARGET_2026-05-20.md) — Soll Core/Live/Rescue/Cloud  
- [`MONOLITH_DECOMPOSITION_PLAN_2026-05-20.md`](MONOLITH_DECOMPOSITION_PLAN_2026-05-20.md) — Phasen A–D  
- [`NO_DUPLICATE_MODULE_RULES.md`](NO_DUPLICATE_MODULE_RULES.md) — Anti-Duplikat-Regeln  
- [`../rescue-stick/RESCUE_STICK_CORE_DEPENDENCIES_2026-05-20.md`](../rescue-stick/RESCUE_STICK_CORE_DEPENDENCIES_2026-05-20.md)

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
