# PI-RS-MSI-GUI-003 FAQ (EN)

As of: **2026-07-13**  
Payload: **1.10.0.20** on physical stick · Retest **passed** (session `20260713_003100_boot`)

Details: [MSI_TUI_CONSOLE_ISOLATION_KB_EN.md](../knowledge-base/rescue/MSI_TUI_CONSOLE_ISOLATION_KB_EN.md)

---

## Why was the text UI broken on MSI GE63 despite GUI being blocked?

**Short answer:** PI-RS-MSI-GUI-002 blocked real X11 start (`openvt`, `startx`), but **boot progress** still emitted phase `x11_starting` and the message “Starting graphical interface …”. Boot progress and Whiptail share **tty1**, which visually corrupted the TUI.

**Evidence:** PI-RS-MSI-RETEST-002, session `20260712_111206_boot`.

---

## What does PI-RS-MSI-GUI-003 change?

| Before (1.10.0.15) | After (1.10.0.16) |
|--------------------|-------------------|
| Timeline: `x11_starting` under MSI compat | Timeline: **`tui_mode_selected`** |
| GUI message on tty1 possible | **`gui_progress_allowed=false`** — no GUI text on tty1 |
| No tty1 ownership model | **Console ownership** — no boot-progress writes after TUI handoff |
| Stale `gui-start.log` from old session | **Session ID** + stale guard on evidence mirror |
| Outdated `version.json` inside squashfs | All version carriers synced to **1.10.0.16** |

---

## Is GUI available on MSI again?

**No.** Under MSI compatibility profile (`setuphelfer_msi_compat=1`, `nomodeset`) GUI remains **intentionally disabled**. Text mode is the primary UI.

---

## Is MSI fixed now?

**Yes — physically confirmed.** Session `20260713_003100_boot` with payload **1.10.0.20** via **PI-RS-MSI-AUTO-EVIDENCE-001**: stable TUI ≥120 s, no `x11_starting`, late evidence captured, `lab-auto-result.json` **passed**.

Details: [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md](PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md)

---

## What appears in `boot-timeline.jsonl` after the fix?

Under MSI compat you should **not** see `x11_starting`. Expect e.g.:

- `msi_compat_detected`
- `gui_availability_checked`
- **`tui_mode_selected`**
- optional `gui_skipped` (audit only, not rendered on tty1)

---

## Why does `/api/version` on the old stick still report 1.10.0.12?

The USB stick still carries payload **1.10.0.15**; internal `config/version.json` was not synced during repack. From **1.10.0.16** onward repack writes all carriers consistently.

After **PI-RS-USB-UPDATER-001**, ESP metadata and squashfs internals must match.

---

## How do I spot stale GUI logs?

Check `session_id` and `boot_id` in:

- `SETUP_LOGS/setuphelfer/logs/boot/gui-start.log`
- `SETUP_LOGS/setuphelfer/evidence/boot/gui-availability.json`

If session ID does **not** match the current boot session → **stale**; do not treat as current GUI evidence.

---

## Kernel parameters for MSI retest

```text
setuphelfer_msi_compat=1
nomodeset
nouveau.modeset=0
pci=noaer
setuphelfer_mode=text
setuphelfer_kiosk=0
```

---

## Next operator steps

1. **PI-RS-USB-UPDATER-001** — update stick to **1.10.0.16** (atomic, no manual version edits)
2. Boot GE63, observe TUI stable for **≥2 minutes**
3. Import SETUP_LOGS → **PI-RS-MSI-RETEST-003**

---

## See also

- [RESCUE_MSI_EVIDENCE_FAQ_EN.md](RESCUE_MSI_EVIDENCE_FAQ_EN.md)
- [PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md](../rescue-stick/PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md)
