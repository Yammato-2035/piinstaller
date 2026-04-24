# Learning Loop (DIAG-1.1)

## Verbindliche Regeln

1. Jeder echte Fehlerfall erzeugt mindestens einen `EvidenceRecord`.
2. Jeder neue Root-Cause-Fund prueft:
   - neue Diagnose noetig?
   - bestehende Diagnose erweitern?
   - Matching-Regel schaerfen?
   - FAQ erweitern?
   - Wissensbasis erweitern?
   - Testfall ergaenzen?
3. Ungenaue/teilweise korrekte Diagnoseausgaenge muessen dokumentiert werden.
4. Abweichung zwischen Symptom und echter Ursache muss explizit festgehalten werden.
5. Erfolg ohne Boot-/Funktionsnachweis gilt nicht automatisch als echter Erfolg.

## Pflichtablauf pro Entwicklungsschritt

1. Aenderung/Test durchfuehren.
2. Pruefen:
   - neue Erkenntnis?
   - neuer Fehler?
   - unklarer Diagnosefall?
   - relevanter Hardware-/Boot-/Speicherkontext?
3. Wenn ja:
   - `EvidenceRecord` anlegen oder aktualisieren.
   - Katalog/Matcher auf Impact pruefen.
   - Wissensbasis + FAQ aktualisieren.
   - Testfall nachziehen.
4. Abschluss:
   - Kennzeichnen, ob `docs_updated`, `faq_updated`, `catalog_updated`, `tests_added`.

## Technische Anbindung

- Diagnosekatalog bekommt Evidence-Zaehler (`suspected`, `confirmed`, `refuted`).
- Zusätzlich Kontexte:
  - `seen_in_platforms`
  - `common_storage_contexts`
  - `common_boot_contexts`

Keine automatische Selbstumschreibung des Katalogs ohne nachvollziehbare Regeln.

## Optionaler Write-Path (Dev-Helper)

Fuer konsistente neue EvidenceRecords steht ein Helper bereit:

- `scripts/diagnostics/new_evidence_record.py`

Der Helper ersetzt keine Review-Entscheidung; er erzeugt nur ein valides Start-Template.
