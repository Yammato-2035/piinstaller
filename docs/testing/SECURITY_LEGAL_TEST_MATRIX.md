# Security & Legal – Testmatrix (Vorbereitung)

Kurzmatrix für nicht-funktionale Anforderungen. Evidence kann unter `docs/evidence/website/` oder dedizierten Pfaden abgelegt werden.

| ID | Bereich | Test | Erwartung | Status | Evidence |
|----|---------|------|-----------|--------|----------|
| SL-001 | Security | Keine Secrets im Repo | Scan / Review ok | Gelb | manuell + ggf. `security` Workflow |
| SL-002 | Security | Bandit/Ruff CI | konfiguriert; Ausnahmen dokumentiert | Gelb | GitHub Actions |
| SL-003 | Legal | Impressum | vorhanden (Site) | Rot | — |
| SL-004 | Legal | Datenschutz | vorhanden (Site) | Rot | — |
| SL-005 | Legal | Haftung / Nutzungshinweis | konservativ formuliert | Rot | `docs/evidence/release-gates/legal_release_gate.md` |
| SL-006 | Legal | Affiliate-Kennzeichnung | konsistent mit Policy | Rot | `docs/monetization/AFFILIATE_DISCLOSURE.md` |

**Hinweis:** Keine Rechtsberatung durch diese Dokumente.
