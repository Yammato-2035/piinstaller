# Rescue ISO — Wrapper Artifact Detection Fix Verification

**Stand:** Repo-Fix verifiziert (kein Full-Build in diesem Lauf)

| Fix | Status |
|-----|--------|
| `run-controlled-iso-build-with-logging.sh` erkennt `binary.hybrid.iso` | ja |
| `prepare-controlled-live-build-tree.sh` → `--zsync false` | ja |
| `auto/clean` → `binary*.zsync*` | ja |
| `RESCUE-BUILD-ZSYNC-STALE-001` in Wrapper/Diagnostics/Gate | ja |

JSON: `rescue_iso_wrapper_artifact_detection_fix_verification_latest.json`
