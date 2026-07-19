# MSI Lab Auto-Evidence (PI-RS-MSI-AUTO-EVIDENCE-001)

**As of:** 2026-07-13  
**Payload:** 1.10.0.20  
**Status:** **passed**

## Context

After PI-RS-MSI-GUI-003 (TUI isolation), retests 003/003B still required manual late-evidence steps; the RS-011B collector ran too early (~10 s).

PI-RS-MSI-AUTO-EVIDENCE-001 automates the full lab boot pipeline on MSI hardware.

## Flow

1. **GRUB:** MSI entry first, `timeout=3`, lab cmdline flags
2. **Boot:** Backend starts; `auto-msi-evidence` does **not** block on `media-check` / `start-assistant`
3. **Late gate:** Uptime ≥ `late_sec + 30` (default: 150 s)
4. **Collect:** `collect-msi-rs011b-evidence.sh`
5. **Eval:** `lab-auto-result.json` via `rescue_msi_lab_evidence_eval.py`
6. **Shutdown:** `evidence_complete`
7. **Failsafe:** 420 s timer only if step 6 does not run

## Regressions (fixed)

| Symptom | Cause | Fix (payload) |
|---------|-------|---------------|
| Shutdown ~12 s | Failsafe service linked into `multi-user.target` | 1.10.0.19 |
| Shutdown 7 min, no collect | Blocking `systemctl start start-assistant` | 1.10.0.20 |

## Evidence on stick

```text
SETUP_LOGS/setuphelfer/evidence/msi-rs011b/lab-auto-result.json
SETUP_LOGS/setuphelfer/evidence/msi-rs011b/late-evidence-auto-*.txt
SETUP_LOGS/setuphelfer/evidence/boot/boot_state_redacted.json
```

Import:

```bash
./scripts/rescue/import-msi-rs011b-evidence.sh /media/$USER/SETUP_LOGS
```

Accepts SETUP_LOGS mount **or** direct `msi-rs011b` path.

## CSE dashboard

After import: fixtures under `setuphelfer-cloudserver-edition/tests/fixtures/rescue_boot_evidence_preview/`.  
API: `GET /api/cloudserver/lab-control-plane/rescue-boot-evidence-preview`

## See also

- FAQ: [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md](../../faq/PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md)
- Summary: [PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md](../../evidence/pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md)
- TUI isolation: [MSI_TUI_CONSOLE_ISOLATION_KB_EN.md](MSI_TUI_CONSOLE_ISOLATION_KB_EN.md)
