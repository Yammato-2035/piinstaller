# Rescue Developer Controlled ISO Build — Result (Permission Policy Fix)

**Date:** 2026-05-31  
**HEAD Start:** ee45636
**Branch:** main  
**Version:** 1.7.3.0  
**Run-ID:** `rescue_developer_iso_20260531_100916`

## Runtime gates

| Gate | Result |
|------|--------|
| Runtime-Gate | **OK** |
| Backend-Version-Gate | **OK** |
| `/api/version` | 1.7.3.0 |
| Clean Runtime | **yes** |
| Dev-Server | enabled, local_lab, storage_ok |

## Fehlerursache (prior run `100050`)

```
touch: '.build/config' kann nicht berührt werden: Keine Berechtigung
```

Root-owned `.build/` (60 Pfade) aus früherem `sudo lb build`. Operator-`sudo rm` entfernte `binary,chroot,cache,local`, nicht `.build/` oder top-level `binary.*`/`chroot.*`/`wget-log*`.

## Policy / Fix implementiert

| Component | Status |
|-----------|--------|
| Permission policy doc | `docs/architecture/RESCUE_CONTROLLED_ISO_BUILD_PERMISSION_POLICY.md` |
| Core module | `backend/core/rescue_iso_build_permission_policy.py` |
| Preflight `permission_policy` | **yes** |
| Clean helper | `scripts/rescue-live/clean-controlled-live-build-tree.sh` |
| Build guard (exit 34) | **yes** — blockiert vor `./auto/config` |

## Clean

| Field | Value |
|-------|-------|
| Dry-run | **OK** — 39 erlaubte Pfade, 38 root-owned |
| Confirm ausgeführt | **nein** (Agent: sudo Passwort erforderlich) |
| sudo nötig | **ja** |
| root-owned danach | **60** (unverändert) |

Operator-Fix:

```bash
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
```

## Preflight

| Field | Value |
|-------|-------|
| Status | **blocked** |
| `permission_policy.operator_fix_required` | **true** |
| `dot_build_writable` | **false** |
| Prior artifacts | 28 (review only, nicht Permission-Blocker allein) |

## Build

| Field | Value |
|-------|-------|
| Gestartet | **nein** (Preflight blocked) |
| Exit code | **n/a** |
| ISO gefunden | **false** |
| ISO SHA256 | **none** |
| Log | `build/rescue/logs/controlled-iso-build/latest.log` |

## Agent / Public Guard

| Check | Result |
|-------|--------|
| Dev Agent local_lab | **OK** |
| Public auto_upload | **false** |
| SSH | **false** |
| write | **false** |

## Safety

USB, dd, Boot, Backup, Restore, apt: **all false / not executed**

## Tests

| Suite | Result |
|-------|--------|
| `test_rescue_developer_iso_build_permission_policy_*` | 10 OK, 1 skipped |
| `test_devserver_agent_*` | 69 OK |

## Entscheidung

| Question | Answer |
|----------|--------|
| Permission policy fix committed | **YES** |
| Tree permission-ready | **NO** — operator sudo clean required |
| ISO built | **NO** |

**Next prompt:** **FIX RESCUE DEVELOPER CONTROLLED ISO BUILD — operator sudo clean, then rebuild**

## References

- `docs/evidence/rescue/RESCUE_DEVELOPER_ISO_BUILD_PERMISSION_ANALYSIS.md`
- `docs/architecture/RESCUE_CONTROLLED_ISO_BUILD_PERMISSION_POLICY.md`
- `docs/evidence/runtime-results/rescue/rescue_developer_controlled_iso_build_preflight.json`
