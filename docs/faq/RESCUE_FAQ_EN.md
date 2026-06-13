# FAQ – Rescue Stick (English)

> Full FAQ (mixed phases): `docs/faq/RESCUE_FAQ.md`  
> R.3 architecture: `docs/architecture/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3_EN.md`

## Where are logs and the test matrix on the stick?

Under **`/setuphelfer-evidence/`**:

| Path | Content |
|------|---------|
| `boot/` | Kernel, UEFI, cmdline |
| `menu/` | TUI menu results |
| `hardware/msi_diagnostics_latest.md` | MSI read-only diagnostics |
| `matrix/rescue_test_matrix_latest.md` | Status matrix (20 areas) |
| `summaries/rescue_evidence_latest.md` | Combined bundle |

## What do matrix statuses mean?

`green` = ok · `yellow` = limited · `red` = failure · `gray` = n/a · `blocked` = intentionally disabled · `unknown` = not evaluated

## Does the stick write to internal disks?

**No.** Only the recognized Setuphelfer rescue stick (or RAM fallback with warning).

## Why no graphical menu / browser?

The current live image has **no browser** and no full display stack (see `docs/evidence/rescue/GRAPHICAL_BOOT_AND_KIOSK_AUDIT_R3.md`). TUI fallback is active.

## How do I trigger evidence collection manually?

```bash
setuphelfer-rescue-evidence.py bundle
```

## When is browser/kiosk available? (R.4)

**Build config** includes chromium + openbox + xorg (from 1.7.17.0). An **existing** stick without a new ISO build still has no browser.

After ISO rebuild (R.5): kiosk autostart via Openbox; evidence at `rescue-ui/kiosk_report_latest.md`.

Details: `docs/architecture/RESCUE_BROWSER_KIOSK_R4_EN.md`
