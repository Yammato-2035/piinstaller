# Deploy-Quelle — Verifikation 2e602d0

**Stand:** 2026-06-02

| Feld | Wert |
|------|------|
| `deploy_source_path` | `/tmp/setuphelfer-deploy-worktrees/piinstaller-2e602d0` |
| `deploy_source_head` | `2e602d0` |
| `deploy_source_clean` | **yes** (`git status --short` leer) |
| `deploy_source_is_committed_head` | **yes** |
| `excluded_workspace_artifacts_not_deployed` | **yes** (Worktree ohne dirty build/qemu/.cursor) |

## Workspace

| Pfad | HEAD | clean |
|------|------|-------|
| `/home/volker/piinstaller` | `2e602d0` | **no** |

## Pre-Deploy-Tests (Quelle Worktree)

| Prüfung | Ergebnis |
|---------|----------|
| Runtime-Import (16 Module) | OK |
| py_compile | OK |
| pytest (15 Dateien) | **55 passed** |
| Frontend build (Worktree + Haupt-`node_modules`) | **fehlgeschlagen** (vite.config Pfad Worktree) — Deploy-Skript baut in `/opt` separat |
| `bash -n` Gate + fleet-session-api | OK |

## Deploy-Ausführung

| Feld | Wert |
|------|------|
| Deploy durchgeführt | **nein** |
| Grund | `deploy_blocked_sudo_required` |

Geplanter Operator-Befehl:

```bash
sudo /tmp/setuphelfer-deploy-worktrees/piinstaller-2e602d0/scripts/deploy-to-opt.sh \
  /tmp/setuphelfer-deploy-worktrees/piinstaller-2e602d0
sudo systemctl restart setuphelfer-backend.service
```
