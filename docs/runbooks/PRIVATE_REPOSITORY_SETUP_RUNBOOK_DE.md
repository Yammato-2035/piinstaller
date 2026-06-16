# Runbook — Einrichtung privates Repository (DE)

**Stand:** 2026-06-16  
**Zielgruppe:** Maintainer mit Zugriff auf Public- und Private-Repos  
**Status:** Prozessbeschreibung — kein automatisierter Deploy

---

## 1. Zweck

Schritt-für-Schritt-Anleitung zur Einrichtung und Pflege eines **privaten Setuphelfer-Repositories** für Cloudserver Edition, Telemetrie-Server, Diagnostikserver, Operator Dashboard und kommerzielle Module — getrennt vom **öffentlichen** `piinstaller`-Repository.

---

## 2. Voraussetzungen

| Nr. | Anforderung |
|-----|-------------|
| 1 | Git-Hosting mit **Private**-Visibility (z. B. GitHub Private, GitLab Private) |
| 2 | Maintainer-Rolle auf Public-Repo |
| 3 | Secret-Manager oder CI-Vault (keine Secrets im Git) |
| 4 | Kenntnis der Boundary-Gates im Public-Repo |
| 5 | Legal-Freigabe für Beta/Produktion (siehe `docs/legal/`) |

---

## 3. Entscheidungsbaum: Public vs. Private

```text
Neues Feature?
    │
    ├─ Facade / Contract / OSS-Doku? ──► Public-Repo
    │
    ├─ Server-Ingest / Billing / Operator-UI? ──► Private-Repo
    │
    └─ Unklar? ──► STOP · Architecture Review · ggf. Handoff-Doc
```

---

## 4. Private Repository anlegen

### 4.1 Repository erstellen

1. Neues Repository mit Visibility **Private** anlegen (Name z. B. `setuphelfer-private`).
2. Default-Branch `main` schützen (PR-Pflicht, Status-Checks).
3. **Kein** Mirror des gesamten Public-Trees — selektive Einbindung.

### 4.2 Basisstruktur

```text
setuphelfer-private/
  README.md                 # Verweis auf Public-Contracts
  backend/
    cloudserver_edition/
    telemetry_server/
    diagnostics_server/
    operator_dashboard/
  commercial/               # licensing, billing (optional)
  infra/
    staging/
  docs/
    handoff/                # Kopien oder Links zu Public-Handoffs
  scripts/
    check-private-import-boundaries.sh
```

### 4.3 Public-Abhängigkeit einbinden (eine Option wählen)

| Option | Vorteil | Nachteil |
|--------|---------|----------|
| **Git Submodule** | Exakte Commit-Pinning | Submodule-Pflege |
| **Package (wheel/npm)** | Saubere Versionierung | Release-Pipeline nötig |
| **Vendor-Copy** | Einfach | Drift-Risiko |

Empfehlung: Submodule auf Public-`main`-Tags für Contract-Dateien.

---

## 5. Boundary-Gates

### 5.1 Public-Repo (vor jedem Push)

```bash
./scripts/check-public-private-boundary.sh
./scripts/check-module-boundaries.sh
```

Erwartung: Kein Exit 10–16 (blocked). Exit 20 = manuelle Review.

### 5.2 Private-Repo

- CI-Job: Import-Richtung prüfen (Private darf Public, nicht umgekehrt)
- Scan auf versehentlich committete Secrets
- Kein Push von Private-Artefakten in Public-Remote

---

## 6. Secrets und Konfiguration

| Secret-Typ | Speicherort | Verboten |
|------------|-------------|----------|
| Telemetry Signing Key | CI-Vault | Git |
| JWT / Session Secret | Operator-Infra | Public-Repo |
| SMTP / Billing API | Secret-Manager | `.env` im Repo |
| Plesk/API-Tokens (Zukunft) | Private CI only | Public-Doku mit echten Werten |

Platzhalter-Domains in Doku: `*.setuphelfer.example`

---

## 7. Handoff-Checkliste (pro Modul)

| Modul | Handoff-Dokument | Owner sign-off |
|-------|------------------|----------------|
| Cloudserver | `docs/private-handoff/CLOUDSERVER_PRIVATE_REPO_HANDOFF.md` | [ ] |
| Telemetrie-Server | `TELEMETRY_INTERNAL_SERVER_HANDOFF.md` | [ ] |
| Diagnostikserver | `DIAGNOSTICS_INTERNAL_SERVER_HANDOFF.md` | [ ] |
| Operator Dashboard | `OPERATOR_DASHBOARD_PRIVATE_HANDOFF.md` | [ ] |
| Plesk Free (später) | `PLESK_FREE_VERSION_FUTURE_HANDOFF.md` | [ ] |

---

## 8. CI/CD (Minimal)

1. **Lint + Unit** auf Private-Code
2. **Contract-Tests** gegen Public `*_contract.py` / OpenAPI
3. **Boundary-Gate** auf beiden Repos
4. **Staging-Deploy** nur aus Private-Pipeline
5. **Kein** Auto-Deploy nach Production ohne Runbook-Freigabe

---

## 9. Synchronisation Public → Private

Bei Contract-Änderungen im Public-Repo:

1. `CONTRACT_VERSION` / OpenAPI `version` prüfen
2. Submodule oder Package bumpen
3. Private Integrationstests ausführen
4. Handoff-Docs bei Breaking Changes aktualisieren

---

## 10. Incident & Rollback

| Szenario | Maßnahme |
|----------|----------|
| Secret im Public-Repo geleakt | Key rotieren, Git-History bereinigen (Owner), Gate erweitern |
| Private-Code in Public-PR | PR schließen, Boundary-Gate analysieren |
| Contract-Drift | Private-Build blockieren bis Sync |

---

## 11. Beta- und Legal-Gates

Vor externem Beta:

- [`docs/legal/BETA_TEST_READINESS_CHECKLIST_DE.md`](../legal/BETA_TEST_READINESS_CHECKLIST_DE.md)
- [`docs/legal/NDA_REQUIRED_ITEMS_DE.md`](../legal/NDA_REQUIRED_ITEMS_DE.md)
- [`docs/legal/BETA_AGREEMENT_REQUIRED_ITEMS_DE.md`](../legal/BETA_AGREEMENT_REQUIRED_ITEMS_DE.md)

---

## 12. Abnahme Einrichtung Private-Repo

- [ ] Repository Private-Visibility verifiziert
- [ ] Nur autorisierte Collaborators
- [ ] Boundary-Gates in CI aktiv
- [ ] Secrets außerhalb Git
- [ ] Handoff-Docs zugewiesen
- [ ] Kein Produktions-Deploy ohne Phase-0-Runtime-Gate (wenn gegen `/opt` getestet)

---

## 13. Referenzen

- [`PUBLIC_PRIVATE_MODULE_BOUNDARIES.md`](../architecture/PUBLIC_PRIVATE_MODULE_BOUNDARIES.md)
- [`SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md`](../architecture/SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md)
- [`docs/evidence/public-private/PUBLIC_PRIVATE_BOUNDARY_RULES.md`](../evidence/public-private/PUBLIC_PRIVATE_BOUNDARY_RULES.md)
