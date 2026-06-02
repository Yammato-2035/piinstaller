# Developer QEMU ISO Rebuild After Autopilot Fix — Result

**Datum:** 2026-06-03  
**HEAD:** `fa9d2b0`

## Ergebnis

| Aspekt | Status |
|--------|--------|
| Post-Fix ISO-Rebuild | **nicht abgeschlossen** |
| Agent Clean | **blocked** (sudo) |
| Agent Build | **blocked** (Exit 30, Policy) |
| Prepare developer-qemu | **ok** (Wants im Config-Tree) |
| ISO auf Disk | **stale** SHA `3ee02b36…`, Autopilot wants **fehlt** in Squashfs |
| Squashfs-Validator | Exit **12** |
| Readiness | **blocked** |

## Kein Fake-Green

Rescue bleibt nicht grün. QEMU-Smoke **nicht** freigegeben.

## Operator-Pflichtsequenz

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu \
  ./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
sudo -v
scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build --profile developer-qemu
./scripts/rescue-live/validate-rescue-iso-squashfs.sh \
  build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
```

Erwartung nach Rebuild: neues SHA ≠ `3ee02b36…`, Squashfs-Validator Exit **0**, Autopilot wants in Squashfs.

Danach: **erneuter Ingest-Lauf** oder QEMU Guest Agent Smoke Operator Run.
