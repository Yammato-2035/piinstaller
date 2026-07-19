# PI-RS-MSI-AUTO-EVIDENCE-001 — Ergebnis

**Status:** `passed`  
**Session:** `20260713_003100_boot` / `961e195f-ae27-4880-abdc-174be2561f83`  
**Payload:** **1.10.0.20**  
**Gerät:** MSI GE63 Raider RGB 8RF (MS-16P5)

## Zusammenfassung

Erster vollautomatisierter MSI-Lab-Boot mit GRUB-Default, Late-Gate (≥120 s), RS-011B-Collect, Eval und Auto-Shutdown **ohne Operator-Eingriff**. Gesamtdauer **~2,5 min**; Shutdown-Phase `auto_shutdown_evidence_complete` (kein 7-min-Failsafe).

## Kriterien

| Kriterium | Ergebnis |
|-----------|----------|
| Payload 1.10.0.20 auf Stick | ja |
| GRUB MSI-Lab-Auto (default=0, timeout=3) | ja |
| Late-Evidence ≥120 s | **153,8 s** Uptime |
| `lab-auto-result.json` | **passed** |
| `console_owner=tui` bei Spät-Capture | ja |
| Boot-Progress-Write blockiert | ja |
| `x11_starting` / GUI-Prozesse | nein |
| Auto-Shutdown nach Collect | ja (~158 s) |
| Failsafe (420 s) | **nicht** ausgelöst |
| CSE-Preview-Fixtures + Tests | importiert, 2/2 passed |

## Auftrag PI-RS-MSI-RETEST-003 / 003B

Diese Session **schließt beide Retest-Aufträge positiv ab**:

- **PI-RS-MSI-RETEST-003:** TUI stabil ≥120 s, kein `x11_starting`, aktuelle Session-Evidence — maschinell belegt.
- **PI-RS-MSI-RETEST-003B:** Spät-Evidence mit `console_owner=tui` und blockiertem Boot-Progress-Write — maschinell belegt.

Frühere Sessions (`20260712_225043`, `20260712_225944`, `20260713_000057`, `20260713_000807`) bleiben als Fehlversuche/Regressionen dokumentiert.

## Evidence

- Import: `docs/evidence/pi_rs_msi_auto_evidence_001/imported-setup-logs/`
- Acceptance: `PI_RS_MSI_AUTO_EVIDENCE_001_ACCEPTANCE.json`
- Stick-Quelle: `/media/.../SETUP_LOGS/setuphelfer/evidence/msi-rs011b/`

## Hinweis

`tui_mode_selected` fehlt weiterhin in `boot-timeline.jsonl` — unter `lab_auto_unattended` nur Warnung, kein Blocker.
