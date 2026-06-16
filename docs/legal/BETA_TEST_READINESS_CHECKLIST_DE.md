# Beta-Test — Readiness-Checkliste (DE)

**Stand:** 2026-06-16  
**Status:** Entwurf / Checkliste — **kein** automatisches „Go“  
**Gilt für:** Geschlossene Beta (Desktop, Rescue, optional private Operator-Services)

---

## 1. Produkt & Technik

| Nr. | Punkt | Status |
|-----|-------|--------|
| 1.1 | `project_version` konsistent (`config/version.json`, Gates) | [ ] |
| 1.2 | Phase-0-Runtime-Gate dokumentiert (wenn gegen `/opt` getestet) | [ ] |
| 1.3 | Backup/Restore/Rescue Kernpfade mit Evidence, nicht nur Unit-Tests | [ ] |
| 1.4 | Public/Private-Boundary-Gate ohne Blocker (Exit 10–16) | [ ] |
| 1.5 | Keine Secrets im Repository oder Beta-Artefakten | [ ] |
| 1.6 | Telemetrie standardmäßig **opt-out** oder `pending_consent` | [ ] |
| 1.7 | Redaction-Preview vor optionalem Telemetrie-Send | [ ] |
| 1.8 | Bekannte Monolith-Risiken dokumentiert (gelb akzeptiert oder mitigiert) | [ ] |

---

## 2. Recht & Verträge

| Nr. | Punkt | Status |
|-----|-------|--------|
| 2.1 | NDA mit Beta-Teilnehmern (siehe `NDA_REQUIRED_ITEMS_DE.md`) | [ ] |
| 2.2 | Beta-Vereinbarung unterzeichnet (`BETA_AGREEMENT_REQUIRED_ITEMS_DE.md`) | [ ] |
| 2.3 | Telemetrie-Einwilligung falls Send aktiv (`TELEMETRY_CONSENT_REQUIRED_ITEMS_DE.md`) | [ ] |
| 2.4 | TOM-Entwurf verfügbar (`TOM_SECURITY_MEASURES_DRAFT_DE.md`) | [ ] |
| 2.5 | Lösch-/Aufbewahrungskonzept (`DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`) | [ ] |
| 2.6 | AVV/DPA mit Auftragsverarbeitern (`PROCESSOR_AGREEMENTS_CHECKLIST_DE.md`) | [ ] |
| 2.7 | Impressum/Datenschutzhinweis für Beta-Kommunikation | [ ] |

---

## 3. Support & Betrieb

| Nr. | Punkt | Status |
|-----|-------|--------|
| 3.1 | Kanal für Fehlerberichte (E-Mail/Ticket) definiert | [ ] |
| 3.2 | SLA-Erwartung **nicht** als Produktion kommuniziert | [ ] |
| 3.3 | Rollback-Pfad für Beta-Builds dokumentiert | [ ] |
| 3.4 | Notfallkontakt Security Incident | [ ] |

---

## 4. Private Services (falls im Beta-Scope)

| Nr. | Punkt | Status |
|-----|-------|--------|
| 4.1 | Telemetrie-/Diagnostikserver nur in privatem Repo | [ ] |
| 4.2 | Operator-Dashboard RBAC getestet | [ ] |
| 4.3 | Cloudserver Edition **nicht** als fertig ausgegeben (wenn zurückgestellt) | [ ] |
| 4.4 | Plesk Free **nicht** im Beta-Scope (Zukunft) | [ ] |

---

## 5. Kommunikation

| Nr. | Punkt | Status |
|-----|-------|--------|
| 5.1 | Beta als „Testversion“ gekennzeichnet | [ ] |
| 5.2 | Bekannte Einschränkungen veröffentlicht | [ ] |
| 5.3 | Keine irreführenden „production ready“-Claims | [ ] |

---

## 6. Freigabe

| Rolle | Name | Datum | Unterschrift |
|-------|------|-------|--------------|
| Product Owner | | | |
| Technical Lead | | | |
| Legal / DPO | | | |

**Hinweis:** Alle Punkte müssen bewusst gesetzt oder mit dokumentierter Ausnahme versehen werden — leere Checkliste ≠ Freigabe.
