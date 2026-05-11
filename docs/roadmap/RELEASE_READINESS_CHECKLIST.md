# Release Readiness – technische Checkliste

Vor Produktionsfreigabe / UG-relevantem Marktauftritt müssen die Punkte **abgehakt und evidenzbasiert** sein.

## Backup / Restore / Verify

- [ ] Full Backup reproduzierbar (Quelle, Ziel, Version dokumentiert)
- [ ] Manifest-Pflicht verifiziert
- [ ] Fehlercodes bei nicht beschreibbarem Ziel geprüft
- [ ] `.partial` / unvollständige Archive werden nicht als gültig akzeptiert
- [ ] Verify Basic und Deep gegen gültiges Archiv grün
- [ ] Verify gegen manipuliertes/beschädigtes Archiv: erwarteter Fehlerpfad
- [ ] Restore nur auf freigegebenes Ziel; interne Systemplatte geschützt
- [ ] Restore Preview ohne Schreiboperation validiert
- [ ] Nach Restore: Boot- und Service-Check dokumentiert

## Hardware & Sicherheit

- [ ] Mindestmatrix Pi 5, Laptop, NVMe, SD, USB, externe SSD (siehe `HARDWARE_TEST_MATRIX.md`)
- [ ] Dualboot / Windows-Umgebung: No-Write-Safety nachgewiesen
- [ ] Keine irreführenden Erfolgsmeldungen in UI/API

## Rescue

- [ ] Read-only Rescue-Flow: Boot, Backend/API, Erkennung, Verify, Bericht (siehe `RESCUE_STICK_TEST_MATRIX.md`)

## Qualität

- [ ] CI grün oder dokumentierte Ausnahmen mit Ticket
- [ ] Keine offenen P0-Blocker (`STATUS_MATRIX.md`)

## Evidence

- [ ] `docs/evidence/release-gates/release_readiness_gate.json` mit `evidence_complete: true` nach Abnahme
