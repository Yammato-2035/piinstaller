# Plesk Free Version — Future Handoff (Private)

**Klassifizierung:** PROPRIETARY · **Zukunft / nicht implementiert**  
**Stand:** 2026-06-16  
**Public-Plan:** [`docs/architecture/PLESK_FREE_VERSION_FUTURE_PLAN.md`](../architecture/PLESK_FREE_VERSION_FUTURE_PLAN.md)

---

## 1. Zweck

Vorbereitende Übergabe für eine **geplante** Plesk-Free-Integration. **Kein** aktiver Entwicklungsauftrag — Dokument dient der späteren Scope-Klärung im Private-Repo.

---

## 2. Voraussetzungen (vor Start)

- [ ] Recovery-Core stabil (Backup/Restore/Rescue)
- [ ] Cloudserver Edition private Pilot abgeschlossen
- [ ] Operator Dashboard + Billing betriebsbereit
- [ ] Rechtliche Klärung Marketplace/Hosting-AGB
- [ ] Product-Owner-Freigabe schriftlich

**Bis dahin:** Kein Code, kein Secret, kein Katalog-Submit.

---

## 3. Geplanter Scope (indikativ)

| Bereich | Beschreibung |
|---------|--------------|
| Panel-Integration | Hosting-Panel-API (Provider-TBD) |
| Provisioning-Hooks | Anbindung an Cloudserver-Orchestrierung |
| Lizenzmodell | „Free“-Tier vs. kostenpflichtige Edition |
| Support-Pfad | Operator-Dashboard-Tickets |

Konkrete API-Versionen und Provider **nicht** in Public-Doku festlegen.

---

## 4. Verboten (Public & vor Freigabe)

- `PLESK_CATALOG_SUBMISSION_SECRET` und echte API-Tokens
- Live-Deploy-Skripte im Public-Repo
- Marketing als „verfügbar“ ohne Produktfreigabe

---

## 5. Private Repository (wenn freigegeben)

```text
backend/
  integrations/
    plesk_free/          # Name TBD
      adapter.py
      catalog_submit.py  # nur mit CI-Secrets
frontend/
  operator/
    plesk_free_panel/    # optional
```

---

## 6. Schnittstellen

| Partner | Nutzung |
|---------|---------|
| `setuphelfer.cloudserver_edition` | Ziel-Host-Provisioning |
| `setuphelfer.operator_private` | Lizenz, Abrechnung |
| Public Core | Backup/Restore auf provisionierten Hosts |

---

## 7. Abnahme (Zukunft)

- [ ] Sandbox-Katalog-Test
- [ ] Keine Regression am OSS-Desktop-Build
- [ ] Legal: Marketplace-Vertrag, AVV
- [ ] FAQ auf „verfügbar“ erst nach Go-Live aktualisieren

---

## 8. Referenzen

- [`PLESK_FREE_VERSION_FUTURE_PLAN.md`](../architecture/PLESK_FREE_VERSION_FUTURE_PLAN.md)
- [`CLOUDSERVER_PRIVATE_REPO_HANDOFF.md`](CLOUDSERVER_PRIVATE_REPO_HANDOFF.md)
- [`OPERATOR_DASHBOARD_PRIVATE_HANDOFF.md`](OPERATOR_DASHBOARD_PRIVATE_HANDOFF.md)
