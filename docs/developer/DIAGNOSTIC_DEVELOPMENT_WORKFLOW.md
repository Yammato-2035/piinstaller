# Diagnostic Development Workflow (verbindlich ab DIAG-1.1)

## Pflicht bei jeder relevanten Aenderung

1. **Aenderung/Test ausfuehren**
2. **Diagnosefragen beantworten**
   - Gab es neue Erkenntnisse?
   - Gab es neue Fehler?
   - Gab es unklare Diagnosefaelle?
   - Gab es relevanten Hardware-/Boot-/Storage-Kontext?
3. **Wenn ja**
   - EvidenceRecord in `data/diagnostics/evidence/` anlegen/aktualisieren.
   - Diagnosen + Matcher pruefen.
   - Doku/FAQ aktualisieren.
   - Tests erweitern.
4. **Review**
   - Sind `docs_updated`, `faq_updated`, `catalog_updated`, `tests_added` korrekt gesetzt?
   - Ist Symptom vs. Root-Cause sauber getrennt?

## Verbote

- Keine losen Chatnotizen als dauerhafte Evidenz.
- Keine automatische Katalog-Umschreibung ohne nachvollziehbare Regel.
- Kein Sammeln irrelevanter Hostdaten.
