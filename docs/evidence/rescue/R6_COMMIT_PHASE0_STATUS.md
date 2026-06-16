# R.6 Commit — Phase 0 Status

**Datum:** 2026-06-10  
**Auftrag:** R.6-COMMIT + R.8 REBUILD VALIDATION PREP

## Git

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD (vor Commit) | `57e30d9` |
| HEAD (nach Commit) | **`d62b4a1`** |
| Letzter Commit | `d62b4a1 feat(rescue): add early boot evidence persistence hook` |
| Push | **erfolgreich** (`main` = `origin/main`) |

## Dirty Tree

Großer Dirty Tree mit vielen **fremden** Änderungen (DCC, Frontend, Build-Tree, R.7-Evidence, Hardware-Runtime, etc.).  
R.6-Commit nimmt **nur** explizit gelistete Dateien auf — kein `git add -A`.

## R.6-Dateien im Workspace

| Datei | Vorhanden |
|-------|-----------|
| `backend/core/rescue_persistence.py` | **ja** (modified) |
| `backend/core/rescue_test_matrix.py` | **ja** (modified) |
| `backend/tests/test_rescue_boot_persistence_hook_r6.py` | **ja** (untracked) |
| `backend/tests/test_rescue_persistence_r3.py` | **ja** (modified) |
| `scripts/.../setuphelfer-rescue-boot-evidence-init` | **ja** (untracked) |
| `scripts/.../setuphelfer-rescue-evidence.py` | **ja** (modified) |
| `scripts/.../setuphelfer-rescue-start-assistant` | **ja** (modified) |
| `scripts/.../prepare-controlled-live-build-tree.sh` | **ja** (modified) |
| R.6 Docs/FAQ/Architektur | **ja** (untracked/modified) |

## Fremdänderungen (nicht stagen)

Beispiele: `network_info_facade.py`, `DevelopmentDashboard.tsx`, `build/rescue/live-build/*`, R.7 `R7_*.md`, `fat32_esp_write_*`, DCC-Evidence, Frontend-Tauri, ckb-next submodule.

## Gate-Status

| Gate | Exit | Befund |
|------|------|--------|
| `check-module-boundaries.sh` | **0** | `review_required`, Warnungen dokumentiert |
| `check-runtime-deploy-gate.sh` | **20** | Legacy-Gate, dev-dashboard 404 (release-Profil) |

## Version (nach Bump + Commit)

`config/version.json`: **1.7.18.0**  
`check_version_consistency.py`: **ok**

## Status

**R.6-Commit abgeschlossen** — kein erneuter Commit erforderlich.  
R.8-Prompt: `docs/evidence/rescue/CAMPAIGN_R8_PROMPT.md`
