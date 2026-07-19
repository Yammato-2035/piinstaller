# PI-RS-MSI-AUTO-EVIDENCE-001 FAQ (DE)

Stand: **2026-07-13**  
Payload: **1.10.0.20** · Status: **passed**

Ausführlich: [MSI_LAB_AUTO_EVIDENCE_KB_DE.md](../knowledge-base/rescue/MSI_LAB_AUTO_EVIDENCE_KB_DE.md)

---

## Was macht der vollautomatische MSI-Lab-Boot?

Der Stick bootet **ohne Tastendruck** in den MSI-Kompatibilitätsmodus, wartet **≥120 s**, sammelt RS-011B-Evidence, schreibt `lab-auto-result.json` und **fährt von selbst herunter** (~2,5 min).

---

## Wie erkenne ich einen erfolgreichen Lauf?

| Indikator | Erwartung |
|-----------|-----------|
| Dauer | ~2,5–3 min (nicht 12 s, nicht 7 min) |
| `boot_state` Phase | `auto_shutdown_evidence_complete` |
| `lab-auto-result.json` | `result_status: passed` |
| Late-Evidence Uptime | ≥ 120 s |

---

## Warum war der Stick früher nach 12 s oder 7 min aus?

- **~12 s:** Failsafe-Service war fälschlich sofort bei `multi-user` aktiv (Payload **1.10.0.19** Fix).
- **~7 min:** `auto-msi-evidence` blockierte auf `media-check` via `start-assistant` (Payload **1.10.0.20** Fix).

---

## Muss ich am MSI noch etwas drücken?

**Nein.** GRUB-Countdown 3 s → Auto-Boot. TUI kann kurz erscheinen; kein Menü-Klick nötig.

---

## Wie importiere ich die Evidence?

```bash
./scripts/rescue/import-msi-rs011b-evidence.sh /media/$USER/SETUP_LOGS
```

Funktioniert mit SETUP_LOGS-Mount **oder** direktem Pfad zu `.../msi-rs011b`.

---

## Wo sehe ich die Daten in der Cloudserver Edition?

Nach Import: CSE-Dashboard-Karte **MSI Rescue Boot Evidence** (Lab-Preview, anonymisiert, kein Live-Send).

---

## Sind PI-RS-MSI-RETEST-003 und 003B damit erledigt?

**Ja — passed.** Session `20260713_003100_boot` schließt beide Retest-Aufträge maschinell ab.

---

## Siehe auch

- [PI_RS_MSI_GUI_003_FAQ.de.md](PI_RS_MSI_GUI_003_FAQ.de.md)
- [RESCUE_MSI_EVIDENCE_FAQ_DE.md](RESCUE_MSI_EVIDENCE_FAQ_DE.md)
- [PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md](../evidence/pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md)
