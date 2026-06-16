# R.8 — R.6 Commit Validation

**Datum:** 2026-06-13  
**Commit:** `d62b4a1`

## `git show --name-only d62b4a1`

Alle erwarteten Dateien **vorhanden**:

| Erwartet | Im Commit |
|----------|-----------|
| `backend/core/rescue_persistence.py` | ✓ |
| `backend/core/rescue_test_matrix.py` | ✓ |
| `scripts/.../setuphelfer-rescue-boot-evidence-init` | ✓ |
| `scripts/.../setuphelfer-rescue-evidence.py` | ✓ |
| `scripts/.../setuphelfer-rescue-start-assistant` | ✓ |
| `scripts/.../prepare-controlled-live-build-tree.sh` | ✓ |
| `backend/tests/test_rescue_boot_persistence_hook_r6.py` | ✓ |

Zusätzlich im Commit: Version-Bump (1.7.18.0), FAQ, R.6-Doku.

## Workspace-Grep

### `initialize_boot_evidence_marker`

| Datei | Zeilen |
|-------|--------|
| `backend/core/rescue_persistence.py` | 356, 434 |
| `scripts/.../setuphelfer-rescue-evidence.py` | 48, 50 |

### `boot_marker`

| Datei | Rolle |
|-------|-------|
| `backend/core/rescue_persistence.py` | schreibt `boot_marker.json` + `.md` |
| `backend/core/rescue_test_matrix.py` | R6-Matrix `boot_marker_written` |
| `scripts/.../setuphelfer-rescue-boot-evidence-init` | Kommentar/Wrapper |
| `scripts/.../setuphelfer-rescue-evidence.py` | `boot_marker_written` Exit-Code |

### `setuphelfer-rescue-boot-evidence-init`

| Datei | Referenz |
|-------|----------|
| `prepare-controlled-live-build-tree.sh` | Staging-Liste Zeile 300 |
| `setuphelfer-rescue-start-assistant` | Aufruf Zeilen 24–25 |

## Bewertung

**PASS** — R.6-Commit vollständig und im Workspace konsistent mit HEAD.
