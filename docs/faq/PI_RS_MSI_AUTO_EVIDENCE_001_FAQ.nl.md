# PI-RS-MSI-AUTO-EVIDENCE-001 FAQ (NL)

Stand: **2026-07-13**  
Payload: **1.10.0.20** · Status: **passed**

---

## Wat doet de volledig automatische MSI-lab-boot?

De stick start **zonder toetsen** in MSI-compatibiliteitsmodus, wacht **≥120 s**, verzamelt RS-011B-evidence, schrijft `lab-auto-result.json` en **schakelt uit** (~2,5 min).

---

## Hoe herken ik een geslaagde run?

| Indicator | Verwacht |
|-----------|----------|
| Duur | ~2,5–3 min |
| `boot_state` fase | `auto_shutdown_evidence_complete` |
| `lab-auto-result.json` | `result_status: passed` |

---

## Evidence importeren

```bash
./scripts/rescue/import-msi-rs011b-evidence.sh /media/$USER/SETUP_LOGS
```

---

## Zie ook

- [RESCUE_MSI_EVIDENCE_FAQ_NL.md](RESCUE_MSI_EVIDENCE_FAQ_NL.md)
- [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md](PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md)
