# Dirty Deploy Audit — Version 1.7.3.0

**Date:** 2026-05-31  
**Branch:** main  
**HEAD (initial audit):** 8aebf99  
**HEAD (clean deploy):** 56ff87c  
**Runtime:** `/opt/setuphelfer`  
**Workspace:** `/home/volker/piinstaller`  

## Ziel

Prüfen, ob `deploy-to-opt.sh` uncommitted Workspace-WIP nach `/opt` kopiert hat.

## Dirty Tree (Workspace)

| Kategorie | Anzahl |
|-----------|--------|
| `git status --short` Einträge gesamt | 43 |
| Modified tracked (`git diff --name-only`) | 17 |
| Untracked (`git ls-files --others --exclude-standard`) | 26 |

## Deploy-Drift-Gate (Manifest-Kern)

| Check | Result |
|-------|--------|
| `deploy_drift.status` (via `/api/dev-dashboard/status`) | **green** |
| `differing_files_count` | 0 |
| `manifest_match` | true |
| Geprüfte Kerndateien | 10 (app.py, versioning, dev_dashboard, version.json, …) |

**Hinweis:** Das Gate prüft nur Manifest-Kerndateien, nicht den gesamten Workspace-Baum.

---

## Vorher (initial audit, 2026-05-31)

### WIP-Dateien in `/opt` (SHA256-Match Workspace = Runtime): **22**

Modified tracked (16) + untracked kritisch (4):

```
backend/core/rescue_iso_build_logs.py
backend/tests/test_rescue_iso_build_logs_v1.py
frontend/src/components/dev-dashboard/RescueBuildLogPanel.tsx
frontend/public/dev-dashboard.snapshot.json
(+ 16 modified tracked Dateien, siehe Git diff)
```

**Bewertung:** Runtime nicht HEAD-clean. ISO Dry-Build **BLOCKED**.

---

## Nachher (clean HEAD deploy, 2026-05-31)

Methode: detached Worktree `/tmp/setuphelfer-clean-deploy` @ `56ff87c`, rsync nach `/opt`, Orphan-WIP aus `/opt` entfernt.

Siehe: `docs/evidence/runtime-results/deploy/CLEAN_HEAD_DEPLOY_1_7_3_0.md`

| Metrik | Result |
|--------|--------|
| WIP SHA256-Matches | **0** |
| Kritische untracked in `/opt` | **ABSENT** (alle 4) |
| `/opt` entspricht clean HEAD | **JA** (Stichprobe verifiziert) |
| Workspace dirty | unverändert (43 Einträge) |

**Bewertung:** Runtime HEAD-clean. ISO Dry-Build **FREIGEGEBEN**.

---

## Ursache (unverändert)

`scripts/deploy-to-opt.sh` kopiert den **gesamten Workspace-Baum** (nicht nur committed HEAD). Uncommitted und untracked Dateien im Workspace werden mit deployed.

## Remediation

Clean detached Worktree + Deploy daraus. Runbook: `docs/runbooks/CLEAN_HEAD_RUNTIME_DEPLOY_RUNBOOK_DE.md`

## Status

| Area | Vorher | Nachher |
|------|--------|---------|
| Manifest-Kern-Drift | GREEN | GREEN |
| Workspace-Cleanliness vs Runtime | BLOCKING | **GREEN** |
| ISO Dry-Build | BLOCKED | **FREIGEGEBEN** |
