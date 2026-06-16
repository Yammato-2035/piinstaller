# Kampagne R.5A — Rebuild-Prompt (nach Remediation)

**Voraussetzung:** Remediation abgeschlossen, Status `tree_ready_for_rebuild`, Validator Exit 0.

## Preflight (Operator)

```bash
cd /home/volker/piinstaller
git rev-parse --short HEAD   # erwartet: 57e30d9 oder neuer mit gleicher Package-List/Bundle-Policy
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
# Exit 0 erforderlich

# Optional vor Rebuild: root-owned lb-Artefakte entfernen
cd build/rescue/live-build/setuphelfer-rescue-live
sudo ./auto/clean
```

## Controlled ISO Build (nur Operator-Terminal)

```bash
export OPERATOR_ISO_BUILD_FREIGABE=1
export SETUPHELFER_RESCUE_BUILD_PROFILE=standard

./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile standard \
  --run-id r5a_rebuild_$(date -u +%Y%m%d_%H%M%S)
```

## Post-Build (R.5A Validation Suite)

Nach erfolgreichem Build (`LB_EXIT=0`):

1. **ISO SHA256** — `sha256sum build/.../binary.hybrid.iso`
2. **SquashFS-Komponentencheck** — chromium, openbox, Xorg, R.3 Core-Module, kiosk-*, evidence.py
3. **GRUB post-build** — Theme-Assets, `grub.cfg` `set theme=`
4. **Entscheidung** — `ready_for_r5b_usb_write` vs. `blocked_missing_runtime_components`

## Erwartete Verbesserungen ggü. fehlgeschlagenem Build `r5a_operator_20260613_153008`

| Komponente | Vorher (blocked) | Nach Rebuild erwartet |
|------------|------------------|----------------------|
| Package-List | 37 Zeilen | 48 Zeilen |
| `source_head` | `a8de59e` | `57e30d9` |
| chromium / openbox / Xorg | MISSING | FOUND |
| R.3 Core-Module | MISSING | FOUND |

## Verboten ohne separate Freigabe

- USB-Write (`OPERATOR_USB_WRITE_FREIGABE=1`)
- MSI-Boot
- Deploy / systemctl gegen Produktiv-Runtime

## Remediation-Referenz

- `R5A_REMEDIATION_PHASE0.md`
- `R5A_PACKAGE_LIST_DRIFT.md`
- `R5A_PACKAGE_LIST_SYNC.md`
- `R5A_RUNTIME_BUNDLE_SYNC.md`
- `R5A_TREE_VALIDATION_AFTER_REMEDIATION.md`
