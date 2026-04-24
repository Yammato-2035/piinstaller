# HW-TEST-1 Durchfuehrungsleitfaden

## 1) Voraussetzungen pro Testlauf

- Test-ID aus Matrix festgelegt.
- Zielmedium eindeutig gemountet und identifiziert.
- Systemprofil-ID und Medienprofil bekannt.
- Risikoklasse geprueft (`requires_confirmation`, `destructive_risk` bei Bedarf).

## 2) Abbruchkriterien

Sofort abbrechen und `EvidenceRecord` mit `outcome=failed` oder `inconclusive` schreiben bei:

- Zielmedium nicht eindeutig oder verwechselt.
- Schreib-/Mountzustand nicht verifizierbar.
- unerwartete Sicherheitsblocker (Allowlist, Path-Containment).
- Inkonsistenz zwischen geplanter und realer Testumgebung.

## 3) Erfolgsdefinition

Nur bestanden, wenn zutreffend:

- Backup-Artefakt vorhanden und plausibel.
- Verify erfolgreich.
- Restore/Preview erfolgreich (je nach Testziel).
- Post-Restore-Validierung erfolgreich.
- Dienste laufen.
- API erreichbar.
- UI erreichbar.
- Keine manuellen Fixes erforderlich bei deterministischem Endzustand.

## 4) Evidence-Pflicht pro Lauf

Mindestens ein `EvidenceRecord` je realem Lauf:

- `source_type`: `hardware_test` oder passender Typ.
- `scenario`: Test-ID referenzieren.
- `raw_signals`: nur diagnose-relevante Signale.
- `diagnosis_links`: `suspected`/`confirmed`/`refuted`.
- `confirmed_root_cause` nur bei belastbarer Evidenz.

Auch `partial` und `inconclusive` muessen gespeichert werden.

## 5) Nachweise

- API-Resultate (strukturiert, keine unnoetigen Voll-Logs).
- relevante Statussignale (service active, verify status, error code).
- Ergebniszuordnung zur Matrix (`passed`/`failed`/`inconclusive`).
