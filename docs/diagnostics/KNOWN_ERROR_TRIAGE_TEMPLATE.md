# Known Error Triage Template

Vorlage für Knowledge-Base-First-Fehlersuche. Kopieren nach `docs/evidence/diagnostics/known_error_triage_<run_id>.md` oder als JSON nach Schema `known_error_triage.schema.json`.

## 1. Aktueller Fehler

| Feld | Wert |
|------|------|
| Datum | |
| Lauf/Run-ID | |
| Komponente | |
| Fehlertext | |
| Exit-Code | |
| HTTP-Code | |
| Logmarker | |
| Profil | |
| Artefakt (ISO/Squashfs/Deploy) | |
| Commit/HEAD | |

## 2. Suche nach früheren Fällen

**Geprüfte Quellen:**

- `docs/evidence/`
- `docs/knowledge-base/`
- `docs/roadmap/`
- `docs/faq/`
- `CHANGELOG.md`
- relevante Logs/JSON-Dateien

**Suchbegriffe:**

- exakter Fehlertext
- Exit-Code / HTTP-Code
- Komponente
- Run-ID-Muster
- frühere Klassifikation

## 3. Frühere Treffer

| Datum | Evidence | Fehlerklasse | Fix | Ergebnis |
|-------|----------|--------------|-----|----------|
| | | | | |

## 4. Bewertung des früheren Fixes

| Prüfung | Ergebnis |
|---------|----------|
| Fix deployed | yes / no |
| Fix im Artefakt enthalten | yes / no |
| Fix im richtigen Profil getestet | yes / no |
| Fix mit End-to-End-Test belegt | yes / no |
| Fix war vollständig | yes / no / review_required |

## 5. Entscheidung

Eine Klassifikation wählen:

- `known_error_fix_missing`
- `known_error_fix_not_deployed`
- `known_error_fix_not_in_artifact`
- `known_error_fix_incomplete`
- `known_error_wrong_root_cause`
- `known_error_new_secondary_cause`
- `new_error`
- `review_required`

## 6. Nächster Schritt

- Kein erneuter gleicher Lösungsweg, wenn er nicht belegt funktioniert hat.
- Neuer Fix oder Rebuild erst nach Begründung.
- KB/Evidence/Roadmap aktualisieren.
