# Phase 0 — Backend-/Paket-Gate vor Runtime-relevanten Arbeiten

**Ziel:** Kein Cursor-Lauf und kein manueller Schritt, der produktive Runtime, Backup, Restore, Rescue, Deploy, systemd, Paketierung oder Hardware am laufenden System testet, ohne vorher abgesichert zu sein, dass Workspace, API und `/opt/setuphelfer` zusammenpassen.

## Wann zwingend

Vor dem ersten Schritt, der einen der folgenden Bereiche **gegen die echte Runtime** oder **echtes Zielmedium** ausführt:

- Backend (API, Jobs, Runner)
- Installationsbaum `/opt/setuphelfer`
- Backup / Restore / Rescue / Deploy
- systemd-Units, Dienststeuerung
- Paketierung / Installer
- Hardware- oder Zielsystem-Verify

## Checkliste (alle zutreffenden Punkte)

| # | Bedingung | Typische Prüfung |
|---|-------------|------------------|
| 1 | Gate-Skript OK | `./scripts/check-runtime-deploy-gate.sh` → Exit **0** (empfohlen zusätzlich `./scripts/check-backend-version-gate.sh` für `/opt`-Dateiprüfung) |
| 2 | `/api/version` erreichbar | `curl …/api/version` → **200** |
| 3 | `project_version` = Workspace | `runtime_deploy_gate_eval` / Legacy-Gate: Abweichung → Exit **12** bzw. Legacy **14** |
| 4 | Produktive Runtime-Pfad | JSON-Feld `backend_runtime_path` = `/opt/setuphelfer/backend` (wenn gegen diese Runtime getestet wird) |
| 5 | `deploy_drift` sauber | `GET /api/dev-dashboard/status` (ggf. mit `SETUPHELFER_DEV_WORKSPACE_ROOT`) — keine für den Test **relevanten** Backend-/Config-Drifts |
| 6 | Deployment-Manifest | Falls `build/deploy/setuphelfer-deploy-manifest.json` (Workspace) und Runtime-Manifest existieren: `manifest_match` oder dokumentierte, bewusste Abweichung |
| 7 | Dienst aktiv | `systemctl is-active setuphelfer-backend.service` (wird vom Gate-Skript mitgeprüft) |
| 8 | `/opt` nicht hinter gewünschtem Commit | Erwarteten Commit mit tatsächlichem Stand unter `/opt/setuphelfer` abgleichen (Git, Release-Tag, oder interne Deploy-Doku) |

**Umgebungsvariablen** (optional): `scripts/check-backend-version-gate.sh` (`SETUPHELFER_VERSION_URL`, …); `scripts/check-runtime-deploy-gate.sh` (`RUNTIME_GATE_SKIP_DEPLOY_DRIFT`, `RUNTIME_GATE_ALLOW_DEPLOY_DRIFT_GRAY`, …).

## Bei Fehlschlag

1. **STOP** — kein Backup, Restore, HW-Test, produktives Verify, Zielpfadtest.
2. Abschlussbericht: Status **`blocked_runtime_outdated`** (oder **`blocked_update_required`** bei reiner Versionskonfiguration) inkl. Exit-Code und Logauszug.
3. Kein „weiter mit altem `/opt`“-Workaround.
4. Runtime/Paket **aktualisieren**, Dienst neu starten **nur wenn** im Auftrag vorgesehen, Gate **wiederholen**.

## Ausnahmen (explizit im Auftrag benennen)

- Nur **Workspace-Unit-Tests** ohne Live-API (Mocks).
- Nur **Lesen** von Doku/Quellcode ohne Ausführung.

---

*Cursor-Regel (kurz): `.cursor/rules/runtime-phase0-gate.mdc`*
