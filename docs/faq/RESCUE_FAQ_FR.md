> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/faq/RESCUE_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ – Clé de secours (English)

> Full FAQ (mixed phases): `docs/faq/Secours_FAQ.md`  
> R.3 architecture: `docs/architecture/Secours_STICK_LOGGING_AND_TESTMATRIX_R3_EN.md`

## Where are logs and the test matrix on the stick?

Under **`/setuphelfer-evidence/`**:

| Path | Content |
|------|---------|
| `boot/` | Kernel, UEFI, cmdline |
| `menu/` | TUI menu results |
| `hardware/msi_diagNonstics_latest.md` | MSI lecture seule diagNonstics |
| `matrix/Secours_test_matrix_latest.md` | Status matrix (20 areas) |
| `summaries/Secours_evidence_latest.md` | Combined bundle |

## What do matrix statuses mean?

`vert` = ok · `jaune` = limited · `rouge` = failure · `gray` = n/a · `bloqué` = intentionally disabled · `Inconnu` = Nont evaluated

## Does the stick write to Interne disks?

**Non.** Only the recognized Setuphelfer Clé de secours (or RAM fallRetour with Avertissement).

## Why Non graphical menu / browser?

The current live image has **Non browser** and Non full display stack (see `docs/evidence/Secours/GRAPHICAL_BOOT_AND_KIOSK_AUDIT_R3.md`). TUI fallRetour is active.

## How do I trigger evidence collection manually?

```bash
setuphelfer-Secours-evidence.py bundle
```

## When is browser/kiosk available? (R.4)

**Build config** includes chromium + openbox + xorg (from 1.7.17.0). An **existing** stick without a new ISO build still has Non browser.

After ISO rebuild (R.5): kiosk autostart via Openbox; evidence at `Secours-ui/kiosk_report_latest.md`.

Details: `docs/architecture/Secours_BROWSER_KIOSK_R4_EN.md`

## Why is `/setuphelfer-evidence/` missing after the first stick write? (R.6)

The USB writer only places **bootable** files (`EFI/`, `live/`, `setuphelfer/Secours/`). The caNonnical runtime tree **`/setuphelfer-evidence/`** is created **on first live boot** by `setuphelfer-Secours-boot-evidence-init`.

**Succès criterion:** After MSI boot this file must exist:

```
/setuphelfer-evidence/boot/boot_marker.md
```

If Linux/TUI starts but this file is missing, the boot persistence hook is Nont active (old image or write failure).

**RAM fallRetour:** If the stick is mounted lecture seule, evidence goes to `/tmp/setuphelfer-evidence/` — the start assistant shows `Evidence: RAM fallRetour`.

Details: `docs/architecture/Secours_BOOT_PERSISTENCE_R6.md`
