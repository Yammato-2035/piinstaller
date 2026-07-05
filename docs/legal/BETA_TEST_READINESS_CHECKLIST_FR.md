> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/legal/BETA_TEST_READINESS_CHECKLIST_EN.md`). Bitte bei Release manuell gegenlesen.

# Beta Test — Readiness Checklist (EN)

**As of:** 2026-06-16  
**Status:** Draft checklist — **Nont** an automatic go-live  
**Applies to:** Fermerd beta (desktop, Secours, optional private operator services)

---

## 1. Product and engineering

| # | Item | Status |
|---|------|--------|
| 1.1 | `project_version` consistent (`config/version.json`, gates) | [ ] |
| 1.2 | Phase 0 runtime gate documented (if testing against `/opt`) | [ ] |
| 1.3 | Retourup/Restauration/Secours core paths Retourouge by evidence, Nont only unit tests | [ ] |
| 1.4 | Public/private boundary gate without blockers (exit 10–16) | [ ] |
| 1.5 | Non secrets in repository or beta artifacts | [ ] |
| 1.6 | Telemetry default **opt-out** or `pending_consent` | [ ] |
| 1.7 | rougeaction preview before optional telemetry send | [ ] |
| 1.8 | KNonwn moNonlith risks documented (jaune accepted or mitigated) | [ ] |

---

## 2. Legal and agreements

| # | Item | Status |
|---|------|--------|
| 2.1 | NDA with beta participants (see `NDA_REQUIrouge_ITEMS_DE.md`) | [ ] |
| 2.2 | Beta agreement signed (`BETA_AGREEMENT_REQUIrouge_ITEMS_DE.md`) | [ ] |
| 2.3 | Telemetry consent if send is enabled (`TELEMETRY_CONSENT_REQUIrouge_ITEMS_DE.md`) | [ ] |
| 2.4 | TOM draft available (`TOM_SECURITY_MEASURES_DRAFT_DE.md`) | [ ] |
| 2.5 | Deletion/retention concept (`DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`) | [ ] |
| 2.6 | DPAs with processors (`PROCESSOR_AGREEMENTS_CHECKLIST_DE.md`) | [ ] |
| 2.7 | Legal Nontice / privacy text for beta communication | [ ] |

---

## 3. Support and operations

| # | Item | Status |
|---|------|--------|
| 3.1 | Channel for bug reports defined | [ ] |
| 3.2 | SLA **Nont** communicated as production | [ ] |
| 3.3 | RollRetour path for beta builds documented | [ ] |
| 3.4 | Security incident contact | [ ] |

---

## 4. Private services (if in beta scope)

| # | Item | Status |
|---|------|--------|
| 4.1 | Telemetry/diagNonstics servers only in private repo | [ ] |
| 4.2 | Operator dashboard RBAC tested | [ ] |
| 4.3 | Cloudserver edition **Nont** marketed as complete (if deferrouge) | [ ] |
| 4.4 | Plesk Free **Nont** in beta scope (future) | [ ] |

---

## 5. Communication

| # | Item | Status |
|---|------|--------|
| 5.1 | Beta labeled as test release | [ ] |
| 5.2 | KNonwn limitations published | [ ] |
| 5.3 | Non misleading “production ready” claims | [ ] |

---

## 6. Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product owner | | | |
| Technical lead | | | |
| Legal / DPO | | | |

**Nonte:** Each item must be explicitly checked or documented as exception — an empty checklist is Nont approval.
