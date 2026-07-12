# PI-RS-MSI-RETEST-003B — Ergebnis

**Status:** `failed` (Spät-Evidence-Ziel nicht erreicht)  
**Session:** `20260712_225944_boot`  
**Kombiniert mit 003:** `review_required`

## Ziel dieses Auftrags

Maschineller Nachweis **nach ≥120 s** mit `console_owner=tui` und blockiertem Boot-Progress-Write.

## Was gelang

| Kriterium | Ergebnis |
|-----------|----------|
| Neuer Boot (nicht 225043) | ja |
| Payload 1.10.0.16 | ja |
| `x11_starting` in Session-Timeline | **nein** |
| GUI gesperrt | ja |
| openvt/startx/Xorg | nein |
| Session-Isolation | ja |
| Operator: TUI ≥120 s | ja |

## Was fehlte (Failure)

| Kriterium | Ergebnis |
|-----------|----------|
| Capture-Uptime ≥120 s | **nein** (~10,5 s) |
| `console_owner=tui` | **nein** (`boot_progress`) |
| `tui_mode_selected` in Timeline | **nein** |
| Manuelle Spät-Evidence-Datei | **nein** |
| Boot-Progress-Write blockiert nach Handoff | **nicht belegbar** |

## Ursache

Der automatische **RS_011B-Collector** erfasst weiterhin unmittelbar nach Boot (~10 s). Das manuelle Spät-Evidence-Skript aus dem Runbook wurde **nicht** auf dem MSI ausgeführt (keine `late-evidence-003b-*.txt` auf SETUP_LOGS).

## Empfehlung

1. Nächster Boot: **120 s warten**, dann **explizit** das Runbook-Skript ausführen (`docs/test-plans/PI_RS_MSI_RETEST_003B_LATE_EVIDENCE_RUNBOOK.md`).
2. **Nicht** vorher `collect-msi-rs011b-evidence.sh` oder Desktop-Launcher starten.
3. Langfristig (separater Auftrag): Collector-Timing oder dedizierter Late-Capture-Dienst — **nicht** in diesem Retest.

## Status-Matrix

- PI-RS-MSI-RETEST-003B: **failed**
- PI-RS-MSI-RETEST-003: bleibt **review_required**
- PI-RS-MSI-GUI-003: bleibt **GELB** (nicht physisch grün ohne Late-Evidence)

Kein Workspace-Wechsel. Kein PI-RS-TEL-LIVE-001 ohne Freigabe.
