# MSI Lab Auto-Evidence (PI-RS-MSI-AUTO-EVIDENCE-001)

**Stand:** 2026-07-13  
**Payload:** 1.10.0.20  
**Status:** **passed**

## Kontext

Nach PI-RS-MSI-GUI-003 (TUI-Isolation) blieben Retest-003/003B manuell aufwendig: Spät-Evidence musste per Runbook ausgelöst werden, der RS-011B-Collector lief zu früh (~10 s).

PI-RS-MSI-AUTO-EVIDENCE-001 automatisiert den gesamten Ablauf für Lab-Boots.

## Ablauf

1. **GRUB:** MSI-Eintrag an Position 0, `timeout=3`, Lab-Cmdline-Flags
2. **Boot:** Backend startet; `auto-msi-evidence` wartet **nicht** auf `media-check` / `start-assistant`
3. **Late gate:** Uptime ≥ `late_sec + 30` (Standard: 150 s)
4. **Collect:** `collect-msi-rs011b-evidence.sh`
5. **Eval:** `lab-auto-result.json` via `rescue_msi_lab_evidence_eval.py`
6. **Shutdown:** `setuphelfer_rescue_auto_shutdown_if_requested evidence_complete`
7. **Failsafe:** Timer 420 s nur wenn Schritt 6 nicht greift

## Regressionen (behoben)

| Symptom | Ursache | Fix (Payload) |
|---------|---------|---------------|
| Shutdown nach ~12 s | Failsafe-Service in `multi-user.target` | 1.10.0.19 |
| Shutdown nach 7 min, kein Collect | Blockierendes `systemctl start start-assistant` | 1.10.0.20 |

## Evidence auf dem Stick

```text
SETUP_LOGS/setuphelfer/evidence/msi-rs011b/lab-auto-result.json
SETUP_LOGS/setuphelfer/evidence/msi-rs011b/late-evidence-auto-*.txt
SETUP_LOGS/setuphelfer/evidence/boot/boot_state_redacted.json
```

Import:

```bash
./scripts/rescue/import-msi-rs011b-evidence.sh /media/$USER/SETUP_LOGS
```

Akzeptiert SETUP_LOGS-Mount **oder** direkten `msi-rs011b`-Pfad.

## CSE-Dashboard

Nach Import: Fixtures unter `setuphelfer-cloudserver-edition/tests/fixtures/rescue_boot_evidence_preview/`.  
API: `GET /api/cloudserver/lab-control-plane/rescue-boot-evidence-preview`

## Verweise

- FAQ: [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md](../../faq/PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md)
- Zusammenfassung: [PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md](../../evidence/pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md)
- TUI-Isolation: [MSI_TUI_CONSOLE_ISOLATION_KB_DE.md](MSI_TUI_CONSOLE_ISOLATION_KB_DE.md)
