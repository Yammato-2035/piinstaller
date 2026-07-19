# PI-RS-MSI-AUTO-EVIDENCE-001 — Gesamtzusammenfassung

**Stand:** 2026-07-13  
**Status:** **passed** (physischer GE63-Retest)  
**Abschluss-Payload:** **1.10.0.20**  
**Abschluss-Session:** `20260713_003100_boot`

---

## Zielbild (erreicht)

Vollautomatisierter MSI-Lab-Boot vom Setuphelfer-Stick:

1. GRUB bootet ohne Eingriff in den MSI-Kompatibilitätsmodus (3 s Countdown)
2. Spät-Evidence und RS-011B-Collect laufen **≥120 s** nach Boot
3. Ergebnis in `lab-auto-result.json` (Eval)
4. Auto-Shutdown nach erfolgreichem Collect
5. Import → Workspace + CSE-Dashboard-Preview (anonymisiert)

---

## Session-Verlauf (Regression → Fix → Erfolg)

| # | Session | Payload | Dauer | Shutdown-Phase | Ergebnis |
|---|---------|---------|-------|----------------|----------|
| 1 | `20260713_000057` | 1.10.0.18 | ~12 s | `failsafe_timeout` | **Bug:** Failsafe-Service fälschlich in `multi-user.target` |
| 2 | `20260713_000807` | 1.10.0.19 | ~7 min | `failsafe_timeout` | **Bug:** `systemctl start start-assistant` blockierte auf `media-check` |
| 3 | **`20260713_003100`** | **1.10.0.20** | **~2,5 min** | **`evidence_complete`** | **passed** |

---

## Abschluss-Befunde (Session 20260713_003100)

| Kriterium | Wert |
|-----------|------|
| Gerät | MSI GE63 Raider RGB 8RF (MS-16P5) |
| Payload SHA256 | `813a6e882d2214d6d29a45406cbfd8079441c326eae90afbb0131f31159383d5` |
| Late-Evidence Uptime | **153,8 s** |
| Eval Uptime | **157,96 s** |
| `lab-auto-result.json` | `result_status: passed` |
| `console_owner` | `tui` |
| Boot-Progress-Write blockiert | ja |
| `x11_starting` | nein |
| Failsafe (420 s) | nicht ausgelöst |

---

## Software-Fixes (Payload 1.10.0.18 → 1.10.0.20)

| Version | Fix |
|---------|-----|
| **1.10.0.19** | Failsafe nur noch als **Timer** (`OnBootSec=420s`), nicht als `multi-user`-Service |
| **1.10.0.20** | Lab-Auto: kein blockierendes `start-assistant`; kein TUI-Warten; Eval `lab_auto_unattended` |

---

## Abgeschlossene Retest-Aufträge

| Auftrag | Status | Nachweis |
|---------|--------|----------|
| **PI-RS-MSI-RETEST-003** | **passed** | TUI ≥120 s, kein `x11_starting`, Session-Evidence |
| **PI-RS-MSI-RETEST-003B** | **passed** | Spät-Capture, `console_owner=tui` |
| **PI-RS-MSI-GUI-003** | **passed** | via Auto-Lab-Session |
| **PI-RS-MSI-AUTO-EVIDENCE-001** | **passed** | `lab-auto-result.json`, Auto-Shutdown |

---

## Evidence-Pfade

```text
docs/evidence/pi_rs_msi_auto_evidence_001/
  PI_RS_MSI_AUTO_EVIDENCE_001_ACCEPTANCE.json
  PI_RS_MSI_AUTO_EVIDENCE_001_RESULT.md
  imported-setup-logs/
docs/evidence/pi_rs_msi_retest_003/PI_RS_MSI_RETEST_003_ACCEPTANCE.json
docs/evidence/pi_rs_msi_retest_003b/PI_RS_MSI_RETEST_003B_ACCEPTANCE.json
docs/roadmap/STATUS_MATRIX.md
```

CSE-Fixtures: `setuphelfer-cloudserver-edition/tests/fixtures/rescue_boot_evidence_preview/`

---

## Operator-Kurzablauf (Referenz)

```bash
# Stick vorbereiten (Entwicklungsrechner)
./scripts/rescue-live/repack-rescue-squashfs-react-shell.sh
./scripts/rescue-live/update-fat32-esp-live-payload.sh ... --execute-update
./scripts/rescue/configure-stick-msi-lab-auto-grub.sh /media/$USER/SETUPHELFER

# MSI: Stick einstecken, booten, ~2,5 min warten

# Evidence holen
./scripts/rescue/import-msi-rs011b-evidence.sh /media/$USER/SETUP_LOGS
```

---

## Bekannte Warnung (nicht blockierend)

`tui_mode_selected` fehlt in `boot-timeline.jsonl` — unter `lab_auto_unattended` nur Warnung in `lab-auto-result.json`.

---

## Verweise

- Runbook: [PI_RS_MSI_AUTO_EVIDENCE_001_OPERATOR_RUNBOOK.md](../../test-plans/PI_RS_MSI_AUTO_EVIDENCE_001_OPERATOR_RUNBOOK.md)
- Technik: [PI_RS_MSI_AUTO_EVIDENCE_001.md](../../rescue-stick/PI_RS_MSI_AUTO_EVIDENCE_001.md)
- KB: [MSI_LAB_AUTO_EVIDENCE_KB_DE.md](../../knowledge-base/rescue/MSI_LAB_AUTO_EVIDENCE_KB_DE.md)
- FAQ: [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md](../../faq/PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md)
