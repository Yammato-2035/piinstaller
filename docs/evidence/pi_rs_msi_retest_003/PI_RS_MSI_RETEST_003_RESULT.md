# PI-RS-MSI-RETEST-003 — Ergebnis

**Status:** `passed` (superseded by PI-RS-MSI-AUTO-EVIDENCE-001)  
**Abschluss-Session:** `20260713_003100_boot` / Payload **1.10.0.20**

## Historie

| Phase | Session | Status |
|-------|---------|--------|
| Erster physischer Retest | `20260712_225043_boot` (1.10.0.16) | `review_required` — Operator TUI ok, Timeline-Lücke |
| Auto-Lab (Regressionen) | `20260713_000057`, `20260713_000807` | failed — Failsafe-Bugs |
| **Abschluss** | **`20260713_003100_boot` (1.10.0.20)** | **`passed`** |

## Abschluss-Befunde (Session 20260713_003100)

| Kriterium | Ergebnis |
|-----------|----------|
| MSI-Compat, nomodeset | ja |
| TUI ≥120 s stabil | ja (Late-Evidence 153,8 s) |
| `x11_starting` | nein |
| GUI blockiert | ja |
| `console_owner=tui` | ja (Spät-Capture) |
| Boot-Progress-Write blockiert | ja |
| Session-Isolation | ja, Payload 1.10.0.20 |
| Interne Platte | unberührt |

Details: `docs/evidence/pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_RESULT.md`

## Bewertung

**PI-RS-MSI-RETEST-003: passed.** Maschineller Nachweis durch PI-RS-MSI-AUTO-EVIDENCE-001 auf GE63 Raider.
