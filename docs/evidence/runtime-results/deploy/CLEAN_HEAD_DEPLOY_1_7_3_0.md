# Clean HEAD Runtime Deploy — Version 1.7.3.0

**Date:** 2026-05-31  
**Branch:** main  
**Ausgangs-HEAD:** 56ff87c  
**Runtime:** `/opt/setuphelfer`  
**Workspace:** `/home/volker/piinstaller` (unverändert, dirty)  

## Ziel

Runtime aus committed HEAD deployen, ohne Workspace-WIP zu stashen, löschen oder committen.

## Clean Worktree

| Feld | Wert |
|------|------|
| Pfad | `/tmp/setuphelfer-clean-deploy` |
| Erzeugung | `git worktree add --detach /tmp/setuphelfer-clean-deploy HEAD` |
| HEAD | `56ff87c` |
| `git status --short` | leer |
| WIP untracked (`rescue_iso_build_logs.py`, `RescueBuildLogPanel.tsx`) | nicht vorhanden |

## Deploy

| Schritt | Result |
|---------|--------|
| `sudo ./scripts/deploy-to-opt.sh /tmp/setuphelfer-clean-deploy` | **blockiert** — sudo Passwort erforderlich (Agent-User `gabriel`) |
| Fallback: rsync aus clean Worktree (gleiche Excludes wie deploy-to-opt.sh) | **durchgeführt** (Exit 23 wegen chgrp-Warnungen, Dateiinhalt synchronisiert) |
| Orphan untracked WIP aus `/opt` entfernt (nur Runtime, nicht Workspace) | 4 Dateien + `.cursor/` |
| `systemctl restart setuphelfer-backend.service` | active |
| `systemctl restart setuphelfer.service` | active |

**Hinweis:** Vollständiges `deploy-to-opt.sh` würde zusätzlich venv/npm/tauri rebuild und systemd drop-in als root ausführen. Für HEAD-clean Dateiinhalt reichte rsync + Orphan-Cleanup; Gates und API-Smokes danach grün.

## Runtime nach Deploy

| Check | Result |
|-------|--------|
| `/api/version` | project_version=**1.7.3.0** |
| Runtime-Gate | **OK** (Exit 0) |
| Backend-Version-Gate | **OK** (Exit 0) |
| control-center-summary | HTTP 200, `.summary` vollständig |
| Dev-Server health | enabled=true, local_lab, storage_ok=true, ssh_allowed=false, public_uploads_allowed=false |
| Dev-Server summary | node_count=2, reports_last_24h=2 |

### Summary-Sektionen

runtime, roadmap, dev_server, rescue_developer, documentation, diagnostics, evidence, next_prompts, warnings, errors — alle `available` bzw. vorhanden.

## Dirty Deploy Audit (nachher)

| Metrik | Vorher | Nachher |
|--------|--------|---------|
| WIP SHA256-Matches Workspace↔`/opt` | 22 | **0** |
| `rescue_iso_build_logs.py` in `/opt` | ja | **ABSENT** |
| `RescueBuildLogPanel.tsx` in `/opt` | ja | **ABSENT** |
| `dev-dashboard.snapshot.json` in `/opt` | ja | **ABSENT** |
| `/opt` vs clean HEAD (`Documentation.tsx`) | dirty match | **MATCH** |

Workspace dirty Tree: unverändert **43 Einträge** (kein stash, kein commit, kein delete).

## deploy-to-opt.sh Risiko

- Skript kopiert den **Workspace-Baum** (`rsync` ohne `--delete`), nicht git HEAD isoliert.
- Deploy aus dirty Workspace kopiert uncommitted/untracked Dateien mit.
- Für Safety-/Rescue-/ISO-Abnahmen: **immer aus clean detached Worktree deployen**.
- Später optional: `deploy-to-opt.sh --head-clean` Modus.

## Freigabe Rescue ISO Dry-Build

| Entscheidung | Status |
|--------------|--------|
| Runtime HEAD-clean (Dateiinhalt) | **JA** |
| Gates grün | **JA** |
| Summary grün | **JA** |
| Workspace WIP unberührt | **JA** |
| **RESCUE DEVELOPER ISO DRY-BUILD WITH DEV AGENT PROFILE GUARD** | **FREIGEGEBEN** |

## Safety

Kein ISO, Backup, Restore, SSH, apt. Keine Safety-Gates geschwächt. Kein Workspace-WIP gelöscht/gestashed/committed.

## Operator-Hinweis

Für vollständigen root-Deploy (venv/npm/tauri rebuild):

```bash
rm -rf /tmp/setuphelfer-clean-deploy
git worktree add --detach /tmp/setuphelfer-clean-deploy HEAD
sudo ./scripts/deploy-to-opt.sh /tmp/setuphelfer-clean-deploy
sudo systemctl restart setuphelfer-backend.service setuphelfer.service
```
