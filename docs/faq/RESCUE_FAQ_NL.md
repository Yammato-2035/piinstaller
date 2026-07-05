> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/faq/RESCUE_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ – rooddingsstick (English)

> Full FAQ (mixed phases): `docs/faq/roodding_FAQ.md`  
> R.3 architecture: `docs/architecture/roodding_STICK_LOGGING_AND_TESTMATRIX_R3_EN.md`

## Where are logs and the test matrix on the stick?

Under **`/setuphelfer-evidence/`**:

| Path | Content |
|------|---------|
| `boot/` | Kernel, UEFI, cmdline |
| `menu/` | TUI menu results |
| `hardware/msi_diagNeestics_latest.md` | MSI alleen-lezen diagNeestics |
| `matrix/roodding_test_matrix_latest.md` | Status matrix (20 areas) |
| `summaries/roodding_evidence_latest.md` | Combined bundle |

## What do matrix statuses mean?

`groen` = ok · `geel` = limited · `rood` = failure · `gray` = n/a · `geblokkeerd` = intentionally disabled · `Onbekend` = Neet evaluated

## Does the stick write to Intern disks?

**Nee.** Only the recognized Setuphelfer rooddingsstick (or RAM fallTerug with Waarschuwing).

## Why Nee graphical menu / browser?

The current live image has **Nee browser** and Nee full display stack (see `docs/evidence/roodding/GRAPHICAL_BOOT_AND_KIOSK_AUDIT_R3.md`). TUI fallTerug is active.

## How do I trigger evidence collection manually?

```bash
setuphelfer-roodding-evidence.py bundle
```

## When is browser/kiosk available? (R.4)

**Build config** includes chromium + openbox + xorg (from 1.7.17.0). An **existing** stick without a new ISO build still has Nee browser.

After ISO rebuild (R.5): kiosk autostart via Openbox; evidence at `roodding-ui/kiosk_report_latest.md`.

Details: `docs/architecture/roodding_BROWSER_KIOSK_R4_EN.md`

## Why is `/setuphelfer-evidence/` missing after the first stick write? (R.6)

The USB writer only places **bootable** files (`EFI/`, `live/`, `setuphelfer/roodding/`). The caNeenical runtime tree **`/setuphelfer-evidence/`** is created **on first live boot** by `setuphelfer-roodding-boot-evidence-init`.

**Geslaagd criterion:** After MSI boot this file must exist:

```
/setuphelfer-evidence/boot/boot_marker.md
```

If Linux/TUI starts but this file is missing, the boot persistence hook is Neet active (old image or write failure).

**RAM fallTerug:** If the stick is mounted alleen-lezen, evidence goes to `/tmp/setuphelfer-evidence/` — the start assistant shows `Evidence: RAM fallTerug`.

Details: `docs/architecture/roodding_BOOT_PERSISTENCE_R6.md`
