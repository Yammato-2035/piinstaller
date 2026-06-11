# Runner Result Pattern Audit (Phase C.2)

**HEAD-Basis:** `0494001` (C.1 Registry)  
**Runner-Anzahl:** 115  
**Rohdaten:** `runner_result_patterns_raw.txt`, `runner_result_patterns.json`

## Häufige Statuswerte (Textscan)

| Token | Runner mit Vorkommen |
|-------|----------------------|
| `blocked` | 111 |
| `ok` | 106 |
| `review_required` | 94 |
| `ready` | 26 |
| `created` | 9 |
| `failed` | 8 |
| `skipped` | 6 |
| `partial` | 4 |
| `error` | 4 |
| `tested` / `implemented` / `planned_only` | ≤3 |

## Uneinheitliche Statuswerte

- Legacy-Set umfasst **14+** verschiedene Literale; Contract C.2 normiert auf **6** Statuswerte.
- Domänenspezifisch: `skipped_no_change`, `rewritten`, `lab_reported`, `invalid`, `partial` — nicht im Contract-Set.
- `runner_lab_phase_consolidation` nutzt `implemented` / `tested` / `planned_only` als Komponenten-Status.

## Struktur-Abdeckung

| Merkmal | Runner ohne Merkmal |
|---------|---------------------|
| `errors`-Key im Quelltext | 2 |
| `warnings`-Key | 2 |
| `evidence`-Bezug | 9 |
| `status`-Bezug | 3 |
| dict-ähnlicher Return | 1 |

## Runner mit vermutlich nicht-standardisierten Resultaten

- Rewrite/Identifier-Runner: verschachtelte `file_results[]` mit `status: rewritten|skipped_no_change`
- Hardware-Matrix/Handoff-Runner: verschachtelte `ok`/`review_required` pro Handoff
- Lab-Consolidation: Komponenten-Inventar statt Runner-Top-Level-Result

## Risiko für Dashboard / API / Automation

| Risiko | Auswirkung |
|--------|------------|
| Uneinheitliche Status-Literale | DCC/API kann Ergebnisse nicht aggregieren |
| `failed`/`blocked` ohne `errors` | Fehlinterpretation als Erfolg |
| Evidence-Pfade uneinheitlich (`evidence_files`, Pfade in Markdown) | Automatische Evidence-Indexierung bricht |
| Kein `no_execution_performed` | Plan vs. Ausführung nicht unterscheidbar |

## C.2 Maßnahme

- Contract: `backend/deploy/runner_result_contract.py`
- Normalizer für Legacy-Dicts (keine Runner-Migration)
- Empty-Result-Templates pro Registry-Eintrag
- Boundary warn-only für Legacy-Tokens

**Nächster Schritt:** C.3 API Facade konsumiert Contract-Results.
