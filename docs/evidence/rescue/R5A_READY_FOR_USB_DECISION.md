# R.5A — Ready-for-USB Entscheidung

**Datum:** 2026-06-13

## Entscheidung

# **`blocked_missing_runtime_components`**

**Nicht** `ready_for_r5b_usb_write`.

## Kriterien-Checkliste

| Kriterium | Erfüllt |
|-----------|---------|
| ISO neu | **ja** (2026-06-13, neue SHA256) |
| SHA256 neu | **ja** (`4f511322…`) |
| LB_EXIT=0 | **ja** |
| UEFI patch valid | **ja** (validate_exit=0) |
| Browser FOUND | **nein** |
| Display stack FOUND | **nein** |
| Kiosk scripts FOUND | **ja** |
| rescue.html FOUND | **ja** |
| GRUB/UEFI mindestens yellow | **ja** (UEFI green, GRUB yellow) |
| filesystem.squashfs vorhanden | **ja** |
| R.3 Evidence-Module im Image | **nein** |
| R.4 Matrix v4 im Image | **nein** |

## Blocker (Priorität)

1. **Package-Liste Drift** — Build-Tree `setuphelfer.list.chroot` = 37 Zeilen; Git = 48 Zeilen (R.4-Pakete fehlen im Build)
2. **Runtime-Bundle Drift** — `source_head=a8de59e`; R.3 `rescue_*.py` nicht im SquashFS
3. **GRUB Theme** — Assets OK, `set theme` in grub.cfg fehlt (sekundär)

## Empfohlene Remediation vor R.5B

```bash
# 1. Package-Liste aus Git in Build-Tree synchronisieren (48 Zeilen)
git checkout 57e30d9 -- build/rescue/live-build/.../setuphelfer.list.chroot

# 2. Temp-Runtime-Bundle mit HEAD 57e30d9 neu validieren/stagen
./scripts/rescue-live/validate-temp-runtime-bundle.sh …
SETUPHELFER_RESCUE_BUILD_PROFILE=standard ./scripts/rescue-live/prepare-controlled-live-build-tree.sh

# 3. Clean + Rebuild (Operator-Terminal)
export OPERATOR_ISO_BUILD_FREIGABE=1
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build --profile standard

# 4. R.5A Post-Build Validation erneut
```

## USB-Write

**Verboten** bis `ready_for_r5b_usb_write`.
