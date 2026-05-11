# Rescue Build — Workspace Policy

Gilt für **ISO-Erstellung**, Logs und Evidence-Artefakte des Setuphelfer-Rettungssticks.

## Pfade

| Bereich | Pfad |
|---------|------|
| Workspace-Root | `build/rescue/` |
| live-build Arbeitsbaum | `build/rescue/live-build/` |
| ISO-Ausgabe | `build/rescue/output/` |
| Build-/VM-Evidence (Dateien) | `build/rescue/evidence/` |
| Logs | `build/rescue/logs/` |

## Regeln

- Alle Build-Artefakte und vom Build-Skript erzeugten Dateien **nur** unter `build/rescue/`.
- **Keine** finalen ISO- oder Image-Artefakte unter `/tmp` ablegen (Staging nur nach Bedarf, Export nach `build/rescue/output/`).
- **Keine** Schreibzugriffe außerhalb dieses Workspace durch die Rescue-Build-Runner und das kontrollierte Build-Skript (keine Host-Root-Änderungen, kein `apt` auf dem Host durch Runner).
- Maximale ISO-Größe: konfigurierbar im Execution-Plan / Result-JSON (`max_iso_bytes`); Überschreitung führt zu **blocked** im Readiness-Gate.
- Logs ausschließlich unter `build/rescue/logs/` (z. B. `iso_build_*.log`, `vm_*.log`).
- Evidence-JSON-Handoffs für Deploy/API bleiben unter `docs/evidence/runtime-results/handoff/`; zusätzliche lokale Kopien dürfen unter `build/rescue/evidence/` liegen.

## USB und echte Geräte

- Kein `dd` auf USB, kein `mount` echter Ziel-Blockgeräte aus diesem Workspace-Strang ohne separates Gate.
