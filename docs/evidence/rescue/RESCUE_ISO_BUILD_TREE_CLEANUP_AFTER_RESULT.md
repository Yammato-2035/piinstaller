# Rescue ISO Build-Tree Cleanup — After Result

**Stand:** 2026-06-02  
**Status:** **cleanup_ok**

## Operator-Cleanup

```bash
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
```

| Feld | Wert |
|------|------|
| **clean_exit** | **0** |
| **Entfernt** | 13 Pfade inkl. **`binary.hybrid.iso`**, `chroot`, `cache`, `.build`, `binary` |

## Nach Cleanup (read-only)

| Prüfung | Vorher | Nachher |
|---------|--------|---------|
| Aktive Mounts | keine | **keine** |
| root-owned unter Build-Tree | ~31501 | **0** |
| `*.iso` / `*.squashfs` | Prior-Artefakte | **keine** |
| Build-Tree Top-Level | binary/chroot/cache | **auto/, config/, evidence/, README** |

## Prepare

```bash
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
```

| Feld | Wert |
|------|------|
| **prepare_exit** | **0** |
| bundle | 2819 files → `includes.chroot/opt/setuphelfer-rescue` |
| manifest | `source_head=e77b83d` |

## Validate

```bash
./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live
```

| Feld | Wert |
|------|------|
| **validate_exit** | **14** |
| Grund | `dangerous_path_override` — `PYTHONPATH=/opt/setuphelfer-rescue` in `setuphelfer-dev-agent.service` |

Cleanup **ok**; Validate **blockiert** separaten Operator-Build-Lauf (kein stale-squashfs mehr).
