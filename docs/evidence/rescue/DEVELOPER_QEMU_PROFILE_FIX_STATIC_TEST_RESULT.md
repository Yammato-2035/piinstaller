# Developer QEMU Profile Fix — Static Test Result (Phase 6)

**Datum:** 2026-06-02

## Bash-Syntax

```bash
bash -n scripts/rescue-live/prepare-controlled-live-build-tree.sh   # OK
bash -n scripts/rescue-live/validate-controlled-live-build-tree.sh # OK
bash -n scripts/rescue-live/run-qemu-developer-iso-smoke.sh         # OK
bash -n scripts/rescue-live/qemu-guest-agent-smoke-operator.sh      # OK
```

## Grep-Prüfung

Log: `developer_qemu_profile_fix_static_check_latest.log`

Erwartete Treffer:
- `console=ttyS0` in `auto/config` (developer-qemu Prepare)
- `setuphelfer-qemu-smoke-autopilot.service` im Profil-Overlay
- `http://10.0.2.2:8001` in Autopilot-Unit
- `assert_developer_qemu_iso_ready` in QEMU-Smoke-Skript

## Python-/Unit-Tests

```bash
PYTHONPATH=backend:. python3 -m unittest \
  backend.tests.test_rescue_developer_qemu_profile_preflight_v1 \
  backend.tests.test_rescue_qemu_smoke_autopilot_profile_v1 -q
```

Ergebnis: **15 tests OK**. Volle `pytest`-Suite nicht ausführbar (`No module named pytest` in Runtime-/System-Python).

## Status

**review_required**

Begründung: Profil-Fix und Unit-Tests grün; `validate-controlled-live-build-tree.sh` Exit **11** wegen root-owned stale `binary/live/filesystem.squashfs` vom vorherigen Standard-Build (nicht durch Profil-Fix verursacht; Entfernung erfordert Operator-`sudo ./auto/clean`).
