# PI-RS-MSI-AUTO-EVIDENCE-001 FAQ (FR)

Date : **2026-07-13**  
Payload : **1.10.0.20** · Statut : **passed**

---

## Que fait le boot lab MSI entièrement automatique ?

La clé démarre **sans action** en mode compatibilité MSI, attend **≥120 s**, collecte l'evidence RS-011B, écrit `lab-auto-result.json` et **s'éteint** (~2,5 min).

---

## Comment reconnaître un run réussi ?

| Indicateur | Attendu |
|------------|---------|
| Durée | ~2,5–3 min |
| Phase `boot_state` | `auto_shutdown_evidence_complete` |
| `lab-auto-result.json` | `result_status: passed` |

---

## Import de l'evidence

```bash
./scripts/rescue/import-msi-rs011b-evidence.sh /media/$USER/SETUP_LOGS
```

---

## Voir aussi

- [RESCUE_MSI_EVIDENCE_FAQ_FR.md](RESCUE_MSI_EVIDENCE_FAQ_FR.md)
- [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md](PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md)
