# Dirty Deploy Audit — Version 1.7.3.0

**Date:** 2026-05-31  
**Branch:** main  
**HEAD:** 8aebf99  
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

## WIP-Dateien in `/opt` (SHA256-Match Workspace = Runtime)

### Modified tracked (16 Treffer)

```
backend/tests/test_rescue_iso_build_dashboard_state_v1.py
docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json
docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md
docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md
docs/evidence/rescue/RESCUE_LIVE_PACKAGE_LIST_DECISION.md
docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json
docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_emulation_manifest.json
docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json
docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json
docs/evidence/runtime-results/rescue/live_build_dpkg_preflight_latest.json
docs/faq/rescue_iso_build_faq.md
docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md
frontend/src/lib/sudoUserMessages.ts
frontend/src/pages/Documentation.tsx
frontend/src/pages/RaspberryPiConfig.tsx
packaging/helpers/setuphelfer-backup-starter.py
```

### Untracked kritisch (4 Treffer, nicht in HEAD)

```
backend/core/rescue_iso_build_logs.py          ← Rescue-ISO WIP Backend
backend/tests/test_rescue_iso_build_logs_v1.py
frontend/src/components/dev-dashboard/RescueBuildLogPanel.tsx
frontend/public/dev-dashboard.snapshot.json
```

## Kritische Bewertung

| Datei | In `/opt` | Aktiv in Runtime | Risiko |
|-------|-----------|------------------|--------|
| `rescue_iso_build_logs.py` | ja | nein (nicht in `app.py` importiert) | mittel — Datei liegt in Runtime, aber kein API-Hook |
| `RescueBuildLogPanel.tsx` | ja | nein (nicht importiert) | niedrig — totales Frontend-WIP |
| `Documentation.tsx` / `RaspberryPiConfig.tsx` | ja | ja (wenn Frontend aus Workspace gebaut) | mittel — UI-Änderungen uncommitted |
| Evidence/Runbook-Dateien | ja | read-only Referenz | niedrig — kein Code-Pfad |

## Ursache

`scripts/deploy-to-opt.sh` kopiert den **gesamten Workspace-Baum** (nicht nur committed HEAD). Uncommitted und untracked Dateien im Workspace werden mit deployed.

## Empfehlung

| Aktion | Status |
|--------|--------|
| Rescue ISO Dry-Build freigegeben | **NEIN — BLOCKING** |
| Grund | Runtime enthält uncommitted WIP (22 Dateien mit SHA256-Match); Runtime ist nicht HEAD-clean |
| Vor ISO-Dry-Build | Option 1: WIP committen, Option 2: WIP stashen + clean redeploy, Option 3: Dry-Build als `dirty-runtime-blocked` markieren |

## Status

| Area | Status |
|------|--------|
| Manifest-Kern-Drift | **GREEN** |
| Workspace-Cleanliness vs Runtime | **YELLOW/BLOCKING** |
| ISO Dry-Build | **BLOCKED** |
