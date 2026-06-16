# R.5 — Operator Gate A (ISO-Build)

## Prüfung

```bash
echo "${OPERATOR_ISO_BUILD_FREIGABE:-0}"
# Ergebnis: 0
```

## Status

**`blocked_operator_iso_build_required`**

Ohne `OPERATOR_ISO_BUILD_FREIGABE=1`:

- kein `lb build`
- kein `run-controlled-iso-build-with-logging.sh`
- Phase 4 übersprungen

## Freigabe durch Operator

```bash
export OPERATOR_ISO_BUILD_FREIGABE=1
cd build/rescue/live-build/setuphelfer-rescue-live
# oder vom Repo-Root:
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh
```

Dokumentation nach Build: `R5_CONTROLLED_ISO_BUILD_LOG.md`
