# 00 – Workspace- und Remote-Gate

## Ergebnis: **passed**

| Prüfung | Erwartung | Ist |
|---------|-----------|-----|
| `pwd` / Git-Root | `/home/volker/piinstaller` | `/home/volker/piinstaller` |
| Repository | `piinstaller` (origin Yammato-2035/piinstaller) | OK |
| Branch | `pi-rs-e2e-live-001d-physical-backup-restore` | OK |
| HEAD | `30aa68b8f359254c3317fb6b8e83b4fef9bc2e89` | OK |
| Ancestor `4535f647` | ja | ja |
| Ancestor `30aa68b8` | ja | ja |
| Remote Branch HEAD | = lokal | `30aa68b8…` |
| `origin/main` | Referenz | `b8651d3337bf30b4443a622fdf8a6c9dc2995df5` |
| Payload SoT | `1.10.0.59` | bestätigt in `config/rescue_payload_version.json` |

## Workspace-Drift

- ~68 geänderte/untracked Dateien (bestehende Fremd-/Lab-Drift, GUI-BVR, Evidence).
- **Nicht zurückgesetzt**, nicht blind gestaged.
- Build erfolgt isoliert aus Commit `30aa68b8` (Worktree).

## Remote-Diagnosemodus

Diagnose-Commits sind auf `origin/pi-rs-e2e-live-001d-physical-backup-restore` vorhanden.
