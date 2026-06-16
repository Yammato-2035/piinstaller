# R.5A Rebuild After Clean — Result

**Datum:** 2026-06-13

## Rebuild gestartet

**nein** — Phase 2 (sudo-Clean) nicht abgeschlossen; Permission-Preflight weiterhin `blocked`.

## Letzter Build-Versuch (Referenz)

| Feld | Wert |
|------|------|
| run_id | `r5a_rebuild_20260613_161300` |
| **LB_EXIT** | **34** |
| error_code | `rescue_iso_build.permission_denied_dot_build` |
| ISO erzeugt | nein |

## Nächste Aktion (Operator, TTY)

### 1. Sudo-Clean

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
find build/rescue/live-build/setuphelfer-rescue-live -maxdepth 2 -user root -print | head -20
# muss leer sein
```

### 2. Rebuild

```bash
export OPERATOR_ISO_BUILD_FREIGABE=1
export SETUPHELFER_RESCUE_BUILD_PROFILE=standard

./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile standard \
  --run-id r5a_rebuild_clean_$(date -u +%Y%m%d_%H%M%S)
```

### 3. Bei LB_EXIT=0

Post-Build Validation (R.5A):

- ISO SHA256
- SquashFS Komponentencheck (chromium, R.3 Module, kiosk-*)
- GRUB post-build
- `ready_for_r5b_usb_write` Entscheidung

## Verboten

Kein USB-Write, kein MSI-Boot.
