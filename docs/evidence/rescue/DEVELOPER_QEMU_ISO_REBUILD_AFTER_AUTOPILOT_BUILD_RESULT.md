# Developer QEMU ISO Rebuild After Autopilot Fix — Build Result

**Datum:** 2026-06-03

## Agent-Session Build-Versuch

| Feld | Wert |
|------|------|
| Build ausgeführt | **no** (`build_started=false`) |
| build_exit / LB_EXIT | **30** |
| error_code | `blocked_requires_operator_sudo_policy` |
| profile in Start-Zeile | `developer-qemu` |
| POLICY_IS_TTY | false |

## Erfolgreicher vorheriger Build (historisch, **ohne** Autopilot-Wants im Squashfs)

| Feld | Wert |
|------|------|
| Log | `build/rescue/logs/controlled-iso-build/2026-06-02T23-43-35+02-00.log` |
| run_id | `rescue_developer_iso_20260602_214335` |
| LB_EXIT | 0 |
| profile | developer-qemu |
| ISO SHA | `3ee02b364bf5a35106591b67fb975f0864390cb413088c0d000e54e770dd48c1` |

## Post-Fix-Rebuild

**Nicht abgeschlossen** — kein neues ISO nach `fa9d2b0`.

## Status

**blocked_build_requires_operator_terminal**

Operator (Terminal 6):

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu \
  ./scripts/rescue-live/prepare-controlled-live-build-tree.sh
sudo -v
scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build --profile developer-qemu
```

Erste Log-Zeile muss `profile=developer-qemu` zeigen.
