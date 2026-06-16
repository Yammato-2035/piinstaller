# R.5A — Controlled ISO Build Log

## Agent-Versuch (2026-06-13)

```bash
export OPERATOR_ISO_BUILD_FREIGABE=1
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build --profile standard --run-id r5a_20260613_152330
```

| Feld | Wert |
|------|------|
| Exit | **30** |
| `build_started` | **false** |
| `error_code` | `blocked_requires_operator_sudo_policy` |
| `next_action` | `manual_operator_terminal_required` |

Summary: `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`

## Operator-Befehl (korrekt, im echten Terminal)

```bash
cd /home/volker/piinstaller
export OPERATOR_ISO_BUILD_FREIGABE=1
export SETUPHELFER_RESCUE_BUILD_PROFILE=standard

# Optional bei Validator Exit 11 (stale chroot):
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean

./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live

./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile standard \
  --run-id r5a_operator_$(date -u +%Y%m%d_%H%M%S)
```

Log: `build/rescue/logs/controlled-iso-build/latest.log`

## Stale ISO (Referenz, nicht R.5A-Ziel)

| Feld | Wert |
|------|------|
| Pfad | `binary.hybrid.iso` |
| Datum | 2026-06-07 |
| SHA256 | `c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194` |

**Kein neuer Build** in R.5A Agent-Session abgeschlossen.
