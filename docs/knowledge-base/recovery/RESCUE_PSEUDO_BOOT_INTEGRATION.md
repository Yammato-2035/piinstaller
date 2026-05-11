# Rescue — Pseudo-Boot-Integration (Strict)

## Kurzbeschreibung

Die Pseudo-Boot-Phase materialisiert **keinen** echten Kernel- oder ISO-Start. Sie beschreibt die erwartete Reihenfolge von EFI über initrd bis Operator-UI, simuliert Service-Startup-Metadaten, dokumentiert Overlay-/Shutdown-Strategie und prüft Backend-Pfade sowie die Rescue-UI-Oberfläche **InspectRun** statisch.

## Artefakte

| Relativer Pfad | Rolle |
|----------------|--------|
| `build/rescue/pseudo_boot_manifest.json` | Neunstufige Boot-/Overlay-/Runtime-Kette |
| `build/rescue/service_startup_simulation.json` | Backend-Unit, Health-Endpunkte, Route-Flags |
| `build/rescue/overlay_boot_strategy.json` | lower/upper/work, keine Default-Persistenz |
| `build/rescue/backend_health_integration.json` | Statische Erkennung `/api/version`, `/health`, Netzwerk, Rescue-Routen |
| `build/rescue/recovery_ui_integration.json` | InspectRun + Dist-Assets, Legacy-Scan nur InspectRun |
| `docs/evidence/runtime-results/handoff/rescue_pseudo_boot_safety_validation.json` | Routen-/Token-Scan (kein Runner-Selbstscan) |
| `docs/evidence/runtime-results/handoff/rescue_pseudo_boot_final_readiness.json` | Aggregation inkl. Artefakt-Gate, Branding, Zero-State |

## Final-Gate

**ready** nur bei vollständigen Inputs, Branding ok, Zero-State nicht blockiert, Overlay-Policy konsistent, Recovery-UI ohne Legacy in InspectRun, keine verbotenen Images unter `build/rescue/` (Ausnahme `build/rescue/output/` wie bei Artefakt-Pipeline).

## Verwandt

- `docs/deploy/DEPLOY_RESCUE_PSEUDO_BOOT_INTEGRATION_DE.md` / `_EN.md`
- Runner: `backend/deploy/runner_rescue_pseudo_boot_integration.py`
