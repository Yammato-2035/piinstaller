# Developer QEMU Autopilot Enable — Test Result

**Datum:** 2026-06-03

## Bash-Syntax

```bash
bash -n scripts/rescue-live/prepare-controlled-live-build-tree.sh   # OK
bash -n scripts/rescue-live/validate-controlled-live-build-tree.sh # OK
bash -n scripts/rescue-live/validate-rescue-iso-squashfs.sh         # OK
```

## Unit-Tests

```bash
python3 -m unittest \
  backend.tests.test_rescue_iso_developer_qemu_autopilot_v1 \
  backend.tests.test_rescue_developer_qemu_profile_preflight_v1 -q
```

**Ergebnis:** 8 tests OK

## Validator-Regression (altes ISO ohne wants)

```bash
validate-rescue-iso-squashfs.sh binary.hybrid.iso  # Exit 12
# SYSTEMD_ENABLE_GAP: setuphelfer-qemu-smoke-autopilot.service not enabled
```

→ Neuer Check erkennt developer-qemu-ISO ohne Autopilot-wants korrekt.

## Bewertung

| | |
|---|---|
| Validator deckt Autopilot-Enable ab | **yes** |
| Status | **ok** |
