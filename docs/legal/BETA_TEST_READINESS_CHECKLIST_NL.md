> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/legal/BETA_TEST_READINESS_CHECKLIST_EN.md`). Bitte bei Release manuell gegenlesen.

# Beta Test — Readiness Checklist (EN)

**As of:** 2026-06-16  
**Status:** Draft checklist — **Neet** an automatic go-live  
**Applies to:** Sluitend beta (desktop, roodding, optional private operator services)

---

## 1. Product and engineering

| # | Item | Status |
|---|------|--------|
| 1.1 | `project_version` consistent (`config/version.json`, gates) | [ ] |
| 1.2 | Phase 0 runtime gate documented (if testing against `/opt`) | [ ] |
| 1.3 | Terugup/Herstel/roodding core paths Teruged by evidence, Neet only unit tests | [ ] |
| 1.4 | Public/private boundary gate without blockers (exit 10–16) | [ ] |
| 1.5 | Nee secrets in repository or beta artifacts | [ ] |
| 1.6 | Telemetry default **opt-out** or `pending_consent` | [ ] |
| 1.7 | roodaction preview before optional telemetry send | [ ] |
| 1.8 | KNeewn moNeelith risks documented (geel accepted or mitigated) | [ ] |

---

## 2. Legal and agreements

| # | Item | Status |
|---|------|--------|
| 2.1 | NDA with beta participants (see `NDA_REQUIrood_ITEMS_DE.md`) | [ ] |
| 2.2 | Beta agreement signed (`BETA_AGREEMENT_REQUIrood_ITEMS_DE.md`) | [ ] |
| 2.3 | Telemetry consent if send is enabled (`TELEMETRY_CONSENT_REQUIrood_ITEMS_DE.md`) | [ ] |
| 2.4 | TOM draft available (`TOM_SECURITY_MEASURES_DRAFT_DE.md`) | [ ] |
| 2.5 | Deletion/retention concept (`DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`) | [ ] |
| 2.6 | DPAs with processors (`PROCESSOR_AGREEMENTS_CHECKLIST_DE.md`) | [ ] |
| 2.7 | Legal Neetice / privacy text for beta communication | [ ] |

---

## 3. Support and operations

| # | Item | Status |
|---|------|--------|
| 3.1 | Channel for bug reports defined | [ ] |
| 3.2 | SLA **Neet** communicated as production | [ ] |
| 3.3 | RollTerug path for beta builds documented | [ ] |
| 3.4 | Security incident contact | [ ] |

---

## 4. Private services (if in beta scope)

| # | Item | Status |
|---|------|--------|
| 4.1 | Telemetry/diagNeestics servers only in private repo | [ ] |
| 4.2 | Operator dashboard RBAC tested | [ ] |
| 4.3 | Cloudserver edition **Neet** marketed as complete (if deferrood) | [ ] |
| 4.4 | Plesk Free **Neet** in beta scope (future) | [ ] |

---

## 5. Communication

| # | Item | Status |
|---|------|--------|
| 5.1 | Beta labeled as test release | [ ] |
| 5.2 | KNeewn limitations published | [ ] |
| 5.3 | Nee misleading “production ready” claims | [ ] |

---

## 6. Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product owner | | | |
| Technical lead | | | |
| Legal / DPO | | | |

**Neete:** Each item must be explicitly checked or documented as exception — an empty checklist is Neet approval.
