# CI-Analyse: `test_confirmed_count_for_perm_group` (Diagnostics Evidence Mapping)

**Datum:** 2026-05-11  
**Fehler (GitHub Actions):** `AssertionError: unexpectedly None` bei `summary.get("PERM-GROUP-008")`  
**Test:** `tests/test_diagnostics_evidence_mapping_v1.py::TestDiagnosticsEvidenceMappingV1::test_confirmed_count_for_perm_group`

## 1. Reproduktion

- **Lokal (Arbeitskopie mit `data/diagnostics/evidence/*.json` auf der Platte):** Test **grün** — `evidence_summary_map()` enthält `PERM-GROUP-008` mit `confirmed >= 1` (z. B. aus `EVID-2026-HW1-01.json`, `diagnosis_links[].status == "confirmed"`).
- **CI:** Repository-Checkout enthielt **keine** Evidence-JSONs unter `data/diagnostics/` → `load_evidence_records()` lieferte **0** Datensätze → `summary.get("PERM-GROUP-008")` → **`None`**.

## 2. Testbefund

| Aspekt | Inhalt |
|--------|--------|
| API | `evidence_summary_map()` aus `core.diagnostics.evidence_store` |
| Erwartung | Schlüssel **`PERM-GROUP-008`** (Diagnose-ID), Feld **`confirmed`** ≥ 1 |
| Logik | Pro `EvidenceRecord` werden `diagnosis_links` (oder Fallback `matched_diagnosis_ids` als `suspected`) aggregiert; `status == "confirmed"` erhöht `confirmed`. |

## 3. Code- / Pfad-Befund

- `EVIDENCE_DIR = Path(__file__).resolve().parents[3] / "data" / "diagnostics" / "evidence"` — repo-relativ korrekt für `backend/core/diagnostics/evidence_store.py`.
- **`.gitignore`:** Zeile `data/` ignorierte **gesamtes** `data/` inkl. `data/diagnostics/**` → Dateien waren **lokal vorhanden, aber nicht versioniert** → CI-Datenstand leer.

## 4. Ursachenklasse

**E)** Remote/CI hatte einen anderen (leeren) Datenstand als die lokale Arbeitskopie mit Evidence-Dateien — **nicht** ein Mapping-Bug in `evidence_summary_map()` und **kein** veraltetes Assertion-Ziel relativ zum Schema.

## 5. Minimaler Fix

1. **`.gitignore`:** `data/` durch `data/*` ersetzen und **`!data/diagnostics/`** sowie **`!data/diagnostics/**`** ergänzen — weiterhin `data/apps` o. Ä. ignoriert, nur Diagnostik-Pfad explizit versioniert.  
2. **`git add data/diagnostics`** — bestehende Evidence-/Profil-/Matrix-JSONs **unverändert** committen (keine synthetischen Inhalte).

## 6. Betroffene Artefakte

- `data/diagnostics/evidence/*.json` (38 Dateien)  
- `data/diagnostics/profiles/*.json` (6 Dateien)  
- `data/diagnostics/hw_test_1_matrix.json`  
- `docs/evidence/release-gates/diagnostics_evidence_seed_audit_2026-05-11.json` (Zeitstempel / Konsistenz)
