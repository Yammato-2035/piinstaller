# 10 – Hypothesen

| Thema | Bewertung |
|-------|-----------|
| H7 Menü-Hang | medium, **unbestätigt** (keine Input/FD/CPU-Evidence) |
| H4/H6/FD/TTY | low / ungeprüft |
| Payload-Drift | low |
| **Evidence-Persistenz** | **high (dieser Auftrag)** — Run-Root fällt auf `/run` zurück |

```text
leading_hypothesis=undetermined   # für Original-Menüproblem
secondary_blocker=evidence_persistence_run_fallback
confidence_menu=none
recommended_action=additional_targeted_diagnostic + fix_evidence_root_mount (separater Auftrag)
```
