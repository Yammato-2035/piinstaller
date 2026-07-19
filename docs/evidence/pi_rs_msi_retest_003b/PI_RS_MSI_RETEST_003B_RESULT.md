# PI-RS-MSI-RETEST-003B — Ergebnis

**Status:** `passed`  
**Session:** `20260713_003100_boot`  
**Payload:** 1.10.0.20  
**Kombiniert mit 003:** `passed`

## Ziel

Maschineller Nachweis **nach ≥120 s** mit `console_owner=tui` und blockiertem Boot-Progress-Write.

## Ergebnis (Session 20260713_003100)

| Kriterium | Ergebnis |
|-----------|----------|
| Capture-Uptime ≥120 s | **ja** (157,96 s Eval / 153,8 s Late-Evidence) |
| `console_owner=tui` | **ja** |
| Boot-Progress-Write blockiert | **ja** |
| Spät-Evidence-Datei | **ja** (`late-evidence-auto-20260713_003306.txt`) |
| `lab-auto-result.json` | **passed** |
| `x11_starting` | nein |
| Auto-Shutdown nach Collect | ja (`evidence_complete`) |

## Vorheriger Fehlversuch

Session `20260712_225944_boot`: Capture bei ~10,5 s — Collector zu früh, kein Late-Evidence. Behoben durch PI-RS-MSI-AUTO-EVIDENCE-001 (Payload 1.10.0.18–1.10.0.20).

## Status-Matrix

- PI-RS-MSI-RETEST-003B: **passed**
- PI-RS-MSI-RETEST-003: **passed**
- PI-RS-MSI-AUTO-EVIDENCE-001: **passed**

Evidence: `docs/evidence/pi_rs_msi_auto_evidence_001/`
