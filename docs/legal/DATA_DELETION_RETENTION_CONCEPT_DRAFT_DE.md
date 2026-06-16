# Datenlöschung und Aufbewahrung — Konzeptentwurf (DE)

**Stand:** 2026-06-16  
**Status:** **Entwurf** — Fristen mit Legal/DPO abstimmen

---

## 1. Datenkategorien

| Kategorie | Beispiele | Speicherort |
|-----------|-----------|-------------|
| Lokale Backup-Daten | Archive, Manifeste | Nutzergerät / vom Nutzer gewähltes Ziel |
| Rescue-Evidence | JSONL, Logs (redacted) | Stick / `docs/evidence` (Dev) |
| Telemetrie (opt-in) | Envelope nach Redaction | Privater Telemetry Server |
| Diagnostik-Sessions | Findings, Session-IDs | Privater Diagnostics Server |
| Operator/Billing | Kundenkonto, Rechnungen | Private kommerzielle Module |
| Notifications | `notification_events.jsonl` | `/var/lib/setuphelfer/` (Prod) |

---

## 2. Aufbewahrungsfristen (Vorschlag — nicht final)

| Daten | Vorschlag | Löschauslöser |
|-------|-----------|---------------|
| Telemetrie-Roh-Events | 90 Tage | Automatischer Job (privat) |
| Telemetrie-Aggregate | 24 Monate | Rollup + Löschung Roh |
| Diagnostik-Sessions | 180 Tage | Inaktivität + Nutzeranfrage |
| Audit-Events (Operator) | 36 Monate | Gesetzliche Aufbewahrung prüfen |
| Beta-Feedback-Tickets | 12 Monate nach Beta-Ende | Manuell/automatisch |
| Lokale Backups | **Nutzerverantwortung** | Produkt bietet Lösch-UI wo implementiert |

---

## 3. Löschverfahren

### 3.1 Nutzeranfrage (Art. 17 DSGVO)

- [ ] Identitätsprüfung
- [ ] Zuordnung pseudonyme Installations-ID
- [ ] Löschung in Telemetry/Diagnostics Store (privat)
- [ ] Bestätigung an Nutzer (ohne interne Systemdetails)

### 3.2 Automatisch

- [ ] Retention-Jobs auf privatem Server
- [ ] Keine Wiederherstellung aus Soft-Delete ohne dokumentierten Grund

### 3.3 Lokales Produkt

- [ ] Deinstallation: Hinweis auf verbleibende Daten unter `/var/lib/setuphelfer`
- [ ] Rescue-Stick: Nutzer formatiert Medium selbst

---

## 4. Ausnahmen

- Gesetzliche Aufbewahrungspflichten (Rechnungen)
- Anonymisierte Statistiken ohne Personenbezug
- Sicherheitslogs bei aktivem Incident (befristet)

---

## 5. Dokumentation

- [ ] Löschprotokoll (Operator, privat)
- [ ] Jährliche Stichprobe Retention-Einhaltung
- [ ] Verweis in Datenschutzerklärung

---

## 6. Technische Referenzen

- `telemetry_client_contract` — keine PII in Pflichtfeldern
- `redaction_contract` — vor Persistenz auf Server
- Handoff Telemetrie/Diagnostics (private Repos)

---

**Hinweis:** Konkrete Fristen sind Platzhalter bis Legal-Freigabe.
