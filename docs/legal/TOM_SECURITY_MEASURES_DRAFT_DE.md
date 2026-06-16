# TOM — Technische und organisatorische Maßnahmen (Entwurf DE)

**Stand:** 2026-06-16  
**Status:** **Entwurf** — vor Produktion mit DPO/Security finalisieren  
**Geltungsbereich:** Setuphelfer Desktop/Rescue (Public) und geplante private Dienste

---

## 1. Vertraulichkeit

| Maßnahme | Beschreibung | Status |
|----------|--------------|--------|
| Zutrittskontrolle | Physischer Zugang zu Serverräumen / Laptops mit Prod-Secrets | [ ] dokumentiert |
| Zugangskontrolle | RBAC Operator-Dashboard, MFA für Maintainer | [ ] geplant |
| Zugriffskontrolle | Least-Privilege, getrennte Staging/Prod | [ ] geplant |
| Trennungskontrolle | Public vs. Private Repository | [ ] aktiv (Gates) |
| Pseudonymisierung | Telemetrie-Installations-IDs ohne Klartext-PII | [ ] geplant |

---

## 2. Integrität

| Maßnahme | Beschreibung | Status |
|----------|--------------|--------|
| Code-Review | PR-Pflicht Public-Repo | [ ] aktiv |
| Boundary-Gates | `check-public-private-boundary.sh` | [ ] aktiv |
| Signierte Releases | Paket-Integrität (deb/rpm/Tauri) | [ ] teilweise |
| Backup-Integrität | Verify Basic/Deep im Produkt | [ ] im Core |

---

## 3. Verfügbarkeit

| Maßnahme | Beschreibung | Status |
|----------|--------------|--------|
| Runtime-Watchdog | Backend-Recovery (Dokumentation vorhanden) | [ ] gelb |
| Private-Server-HA | Telemetry/Diagnostics (private) | [ ] nicht produktiv |
| Incident-Runbook | Security + Ausfall | [ ] Entwurf |

---

## 4. Belastbarkeit

| Maßnahme | Beschreibung | Status |
|----------|--------------|--------|
| Regelmäßige Updates | OS- und Dependency-Patches | [ ] Prozess |
| Penetrationstests | Vor Beta private Services | [ ] geplant |
| Schwachstellenmanagement | Coordinated Disclosure | [ ] Beta-Agreement |

---

## 5. Verfahren zur regelmäßigen Überprüfung

- [ ] Jährliche TOM-Review
- [ ] Review nach größeren Architekturänderungen (Cloudserver, Operator)
- [ ] Nachweis Schulungen Maintainer (DSGVO-Basics)

---

## 6. Auftragsverarbeitung

Siehe [`PROCESSOR_AGREEMENTS_CHECKLIST_DE.md`](PROCESSOR_AGREEMENTS_CHECKLIST_DE.md)

---

**Hinweis:** Dieser Entwurf ersetzt keine individuelle Datenschutz-Folgenabschätzung (DSFA), falls erforderlich.
