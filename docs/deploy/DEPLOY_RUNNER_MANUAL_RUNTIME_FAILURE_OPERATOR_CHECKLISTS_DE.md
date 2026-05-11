# Manual Runtime Failure Operator Checklists

Operator-Checklisten je Failure-Klasse fuer manuelle, nicht-destruktive Testlaeufe.

- Keine automatische Ausfuehrung/Reparatur/Freigabe/Ingestion/Release
- Nur Testmedien, keine produktiven Datentraeger
- Fokus auf Safety-Checks, Abort-Bedingungen und Evidence

API: `POST /api/deploy/runner/manual-runtime/failure-operator-checklists`
