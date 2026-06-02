# Controlled ISO Build — Chroot/Mount Precheck

**Stand:** 2026-06-02  
**Status:** **`blocked_by_root_owned_leftovers`**

## Mounts

| Prüfung | Ergebnis |
|---------|----------|
| `findmnt -R build/.../setuphelfer-rescue-live` | **keine aktiven Mounts** |
| System-Mounts mit rescue/chroot | **keine** |

→ **Kein** `blocked_by_chroot_mounts` (keine hängenden Mounts).

## Build-Tree-Reste (Jun 1 Prior-Build)

| Pfad | Anmerkung |
|------|-----------|
| `chroot/` | root-owned, vollständiger Chroot-Rest |
| `binary/` | root-owned, inkl. `binary.hybrid.iso` (~512 MB) |
| `cache/`, `.build/` | root-owned Stage-Marker |
| `binary/live/filesystem.squashfs` | vorhanden — `validate-controlled-live-build-tree.sh` meldet **FORBIDDEN** (Stale-Artefakt) |

Preflight (`rescue_developer_controlled_iso_build_preflight.json`): **root_owned_count=31501**, `operator_fix_required=true`.

## Operator-Handoff (kein Cleanup in diesem Lauf)

```bash
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --dry-run
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live
```

## Bewertung

Vor **controlled ISO build operator run**: Cleanup + Re-Prepare erforderlich.
