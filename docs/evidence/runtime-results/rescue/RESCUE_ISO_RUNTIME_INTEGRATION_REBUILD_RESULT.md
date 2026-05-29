# Rescue ISO — Runtime Integration Rebuild Result

**Klassifikation:** `runtime_integration_rebuild_not_executed`

## Grund

`RESCUE_RUNTIME_REBUILD_FREIGEGEBEN` war **nicht** gesetzt. Kein `lb build` aus Agent-Kontext (Policy, kein sudo-TTY).

## Build-Tree

Prepare + DE-Keyboard/Locale/Timezone + systemd-wants: **vorbereitet** (siehe `RESCUE_ISO_RUNTIME_INTEGRATION_BUILD_TREE_VERIFICATION.md`).

## Bestehende ISO (unverändert)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| mtime | 2026-05-29 13:49 |
| Größe | 507510784 |
| `validate-rescue-iso-squashfs.sh` | Exit **12** (systemd enable fehlt; DE-Locale fehlt in Squashfs) |

## Operator — Rebuild

```bash
export RESCUE_RUNTIME_REBUILD_FREIGEGEBEN=1
cd /home/volker/piinstaller
./scripts/check-runtime-deploy-gate.sh
BUILD_TREE=build/rescue/live-build/setuphelfer-rescue-live
findmnt -R "$BUILD_TREE" || true
# keine aktiven Mounts → clean + prepare + run-controlled-iso-build-with-logging.sh --operator-confirm-build
./scripts/rescue-live/validate-rescue-iso-squashfs.sh "$BUILD_TREE/binary.hybrid.iso"
# Ziel: Exit 0
```

JSON: `rescue_iso_runtime_integration_rebuild_result_latest.json`
