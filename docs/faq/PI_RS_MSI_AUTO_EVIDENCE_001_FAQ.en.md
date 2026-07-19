# PI-RS-MSI-AUTO-EVIDENCE-001 FAQ (EN)

As of: **2026-07-13**  
Payload: **1.10.0.20** · Status: **passed**

Details: [MSI_LAB_AUTO_EVIDENCE_KB_EN.md](../knowledge-base/rescue/MSI_LAB_AUTO_EVIDENCE_KB_EN.md)

---

## What does unattended MSI lab boot do?

The stick boots **without keypress** into MSI compatibility mode, waits **≥120 s**, collects RS-011B evidence, writes `lab-auto-result.json`, and **powers off** (~2.5 min).

---

## How do I recognize a successful run?

| Indicator | Expected |
|-----------|----------|
| Duration | ~2.5–3 min (not 12 s, not 7 min) |
| `boot_state` phase | `auto_shutdown_evidence_complete` |
| `lab-auto-result.json` | `result_status: passed` |
| Late evidence uptime | ≥ 120 s |

---

## Why did the stick shut down after 12 s or 7 min earlier?

- **~12 s:** Failsafe service was incorrectly enabled in `multi-user.target` (fixed in payload **1.10.0.19**).
- **~7 min:** `auto-msi-evidence` blocked on `media-check` via `start-assistant` (fixed in payload **1.10.0.20**).

---

## Do I need to press anything on the MSI laptop?

**No.** GRUB 3 s countdown → auto boot. TUI may appear briefly; no menu interaction required.

---

## How do I import evidence?

```bash
./scripts/rescue/import-msi-rs011b-evidence.sh /media/$USER/SETUP_LOGS
```

Works with SETUP_LOGS mount **or** direct path to `.../msi-rs011b`.

---

## Where is data shown in Cloudserver Edition?

After import: CSE dashboard card **MSI Rescue Boot Evidence** (lab preview, anonymized, no live send).

---

## Are PI-RS-MSI-RETEST-003 and 003B complete?

**Yes — passed.** Session `20260713_003100_boot` closes both retests with machine evidence.

---

## See also

- [PI_RS_MSI_GUI_003_FAQ.en.md](PI_RS_MSI_GUI_003_FAQ.en.md)
- [RESCUE_MSI_EVIDENCE_FAQ_EN.md](RESCUE_MSI_EVIDENCE_FAQ_EN.md)
- [PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md](../evidence/pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md)
