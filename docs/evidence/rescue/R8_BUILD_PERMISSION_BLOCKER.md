# R.8 — Build Permission Blocker

**Datum:** 2026-06-13  
**Kampagne:** R.8-BUILD-UNBLOCK

## Symptom

Controlled ISO Build blockiert vor `lb build`:

| Feld | Wert |
|------|------|
| **LB_EXIT** | **34** |
| **error_code** | `rescue_iso_build.permission_denied_dot_build` |
| **permission_status** | `blocked` |

## Permission Preflight (gemessen)

| Feld | Wert |
|------|------|
| `root_owned_count` | **44076** |
| `root_owned_active_count` | **44066** |
| `operator_fix_required` | **true** |
| `permission_blockers` | `root_owned_active_work_areas`, `root_owned_top_level_artifacts` |

Betroffene Bereiche (Sample): `.build/*`, `binary/`, `chroot/`, `cache/`, `binary.hybrid.iso`

## Kontext

| Feld | Wert |
|------|------|
| HEAD | `d62b4a1` (R.6 committed) |
| Build-Tree R.6 | vorbereitet (`source_head=d62b4a1`) |
| Validate (vor Clean) | Exit 11 — stale `binary.hybrid.iso` |

R.6-Inhalt ist **nicht** das Problem — nur root-owned Live-Build-Artefakte vom vorherigen `lb build`.

## recommended_fix

```bash
cd /home/volker/piinstaller
./scripts/rescue-live/clean-controlled-live-build-tree.sh --dry-run
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
```

Danach Operator-ISO-Build mit `--operator-confirm-build`.
