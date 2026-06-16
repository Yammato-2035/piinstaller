# R.7 — R.6 Commit Validation

**Datum:** 2026-06-10  
**HEAD:** `57e30d9`

## Prüfmatrix

| Check | Workspace | Im Stick-Squashfs (aktuell) | Im Git-Commit |
|-------|-----------|----------------------------|---------------|
| `setuphelfer-rescue-boot-evidence-init` | **FOUND** (`scripts/rescue-live/image/`, untracked) | **MISSING** | **nein** |
| `rescue_persistence.py` v4 | **FOUND** (`RESCUE_PERSISTENCE_VERSION = 4`) | **v3** | **nein** (modified) |
| `initialize_boot_evidence_marker` | **FOUND** | **MISSING** | **nein** |
| `setuphelfer-rescue-evidence.py boot-init` | **FOUND** | **MISSING** | **nein** |
| `start-assistant` boot-hook | **FOUND** | **MISSING** | **nein** |
| `test_rescue_boot_persistence_hook_r6.py` | **FOUND** | n/a | **nein** (untracked) |
| Matrix R6 (`build_r6_boot_persistence_matrix_entries`) | **FOUND** | Matrix v4 ja, R6-Einträge **ohne Hook wirkungslos** | **nein** |
| `prepare-controlled-live-build-tree.sh` staging | **FOUND** (boot-evidence-init in Liste) | — | **nein** |

## Unit-Tests (Workspace)

```
backend.tests.test_rescue_boot_persistence_hook_r6 — 5/5 OK
```

## Bewertung

| Kriterium | Status |
|-----------|--------|
| R.6 Code im Workspace vollständig | **ja** |
| R.6 committed | **nein** |
| R.6 im aktuellen ISO/Squashfs/Stick | **nein** |

## Entscheidung

**R.6 workspace-valid, deployment-pending.**  
R.7 Hardware-Nachweis mit **bestehendem Stick (pre-R.6-Image)** kann `boot_marker` **nicht** erfüllen — erwartbar `R7_BOOT_MARKER_MISSING`.
