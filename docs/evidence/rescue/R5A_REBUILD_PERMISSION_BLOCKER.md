# R.5A Rebuild — Permission Blocker (LB_EXIT=34)

**Datum:** 2026-06-13  
**Run-ID (fehlgeschlagen):** `r5a_rebuild_20260613_161300`  
**Profil:** `standard`

## Blocker

| Feld | Wert |
|------|------|
| **LB_EXIT** | **34** |
| **error_code** | `rescue_iso_build.permission_denied_dot_build` |
| **permission_status** | **`blocked`** |
| **build_started** | `false` |
| **no_build_executed** | `true` |

## Root-Owned Artefakte (Preflight)

| Metrik | Wert (vor Cleanup) |
|--------|-------------------|
| `root_owned_count` | **6930** |
| `root_owned_active_count` | **6921** |

Nach partiellem Entfernen von Top-Level-Artefakten (ohne sudo): nur noch **`cache/`** blockiert.

| Metrik | Wert (aktuell) |
|--------|----------------|
| `root_owned_count` | **6695** |
| `root_owned_active_count` | **6695** |
| Verbleibender Blocker | `build/.../setuphelfer-rescue-live/cache` (root-owned) |

## permission_blockers

- `root_owned_active_work_areas`
- `root_owned_top_level_artifacts`

## Sample Paths

```
build/rescue/live-build/setuphelfer-rescue-live/binary          (entfernt → quarantine)
build/rescue/live-build/setuphelfer-rescue-live/binary.contents (entfernt)
build/rescue/live-build/setuphelfer-rescue-live/binary.packages (entfernt)
build/rescue/live-build/setuphelfer-rescue-live/cache           ← BLOCKIERT
build/rescue/live-build/setuphelfer-rescue-live/cache/bootstrap
build/rescue/live-build/setuphelfer-rescue-live/cache/packages.chroot
build/rescue/live-build/setuphelfer-rescue-live/chroot.headers  (entfernt)
build/rescue/live-build/setuphelfer-rescue-live/wget-log*       (entfernt)
```

## recommended_fix (aus Policy-Summary)

```
Run: sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
```

## Log-Auszug (`controlled_iso_build_latest_summary.json`)

```
Run ./scripts/rescue-live/clean-controlled-live-build-tree.sh --dry-run
then sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
LB_EXIT=34
```

## Ursache

Vorheriger Operator-ISO-Build (`lb build`) erzeugte root-owned Working Areas (`binary/`, `cache/`, …). Agent-Shell kann `sudo -n` nicht ausführen (Passwort erforderlich).

## Build-Tree-Inhalt (config)

`config/`, `auto/`, `evidence/` — **unberührt**, Remediation-Stand intakt.
