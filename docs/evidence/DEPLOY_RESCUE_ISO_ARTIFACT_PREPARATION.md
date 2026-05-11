# Evidence — DEPLOY_RESCUE_ISO_ARTIFACT_PREPARATION

## Zweck dieses Evidence-Eintrags

Nachweis, dass die **Strict-Mode-Artefakt-Vorbereitung** für die Rescue-ISO nur kontrollierte Schreibpfade nutzt und **keine** ISO-/IMG-Erzeugung, kein `grub-mkrescue`, kein `xorriso` und kein `dd` aus dem Runner heraus ausführt.

## Erwartete Handoffs

| Datei (relativ zum Repo) | Rolle |
|--------------------------|--------|
| `build/rescue/rootfs_manifest.json` | RootFS-Manifest |
| `build/rescue/frontend_manifest.json` | Offline-Frontend-Analyse |
| `build/rescue/backend_manifest.json` | Backend-/Routen-Nachweis |
| `build/rescue/boot_artifact_manifest.json` | Geplante Boot-Struktur |
| `build/rescue/overlay_persistence_strategy.json` | Overlay/Persistenz-Policy |
| `docs/evidence/runtime-results/handoff/rescue_artifact_readiness_gate.json` | Aggregiertes Gate |
| `docs/evidence/runtime-results/handoff/rescue_iso_final_readiness_gate.json` | Optionaler Input aus ISO-Pipeline |
| `docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json` | Branding-Status |

## Tests

`backend/tests/test_deploy_runner_rescue_iso_artifact_preparation_v1.py` sowie Regression mit Readiness-Pipeline und Branding-Guard.

## Operator-Hinweis

Nach erfolgreicher Kette Evidence-JSON archivieren; Versionsvorschlag siehe Deploy-DE-Doku (manuell 1.8.0).
