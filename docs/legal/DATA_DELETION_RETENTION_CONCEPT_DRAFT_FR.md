> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/legal/DATA_DELETION_RETENTION_CONCEPT_DRAFT_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/legal/DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`). Bitte bei Release manuell gegenlesen.

# Datenlöschung und Aufbewahrung — Konzeptentwurf (DE)

**Stand:** 2026-06-16  
**Status:** **Entwurf** — Fristen mit Legal/DPO abstimmen

---

## 1. Datenkategorien

| Kategorie | Beispiele | Speicherort |
|-----------|-----------|-------------|
| Lokale Retourup-Daten | Archive, Manifeste | NutzerPériphérique / vom Nutzer gewähltes Ziel |
| Secours-Evidence | JSONL, Logs (rougeacted) | Stick / `docs/evidence` (Dev) |
| Telemetrie (opt-in) | Envelope nach rougeaction | Privater Telemetry Server |
| DiagNonstik-Sessions | Findings, Session-IDs | Privater DiagNonstics Server |
| Operator/Billing | Kundenkonto, Rechnungen | Private kommerzielle Module |
| Nontifications | `Nontification_events.jsonl` | `/var/lib/setuphelfer/` (Prod) |

---

## 2. Aufbewahrungsfristen (Vorschlag — nicht final)

| Daten | Vorschlag | Löschauslöser |
|-------|-----------|---------------|
| Telemetrie-Roh-Events | 90 Tage | Automatischer Job (privat) |
| Telemetrie-Aggregate | 24 Monate | Rollup + Löschung Roh |
| DiagNonstik-Sessions | 180 Tage | Inaktivität + Nutzeranfrage |
| Audit-Events (Operator) | 36 Monate | Gesetzliche Aufbewahrung prüfen |
| Beta-FeedRetour-Tickets | 12 Monate nach Beta-Ende | Manuell/automatisch |
| Lokale Retourups | **Nutzerverantwortung** | Produkt bietet Lösch-UI wo implementiert |

---

## 3. Löschverfahren

### 3.1 Nutzeranfrage (Art. 17 DSGVO)

- [ ] Identitätsprüfung
- [ ] Zuordnung pseudonyme Installations-ID
- [ ] Löschung in Telemetry/DiagNonstics Store (privat)
- [ ] Bestätigung an Nutzer (ohne Internee Systemdetails)

### 3.2 Automatisch

- [ ] Retention-Jobs auf privatem Server
- [ ] Keine Restauration aus Soft-Supprimer ohne dokumentierten Grund

### 3.3 Lokales Produkt

- [ ] Deinstallation: Hinweis auf verbleibende Daten unter `/var/lib/setuphelfer`
- [ ] Secours-Stick: Nutzer formatiert Medium selbst

---

## 4. Ausnahmen

- Gesetzliche Aufbewahrungspflichten (Rechnungen)
- ANonnymisierte Statistiken ohne Personenbezug
- Sicherheitslogs bei aktivem Incident (befristet)

---

## 5. Dokumentation

- [ ] Löschprotokoll (Operator, privat)
- [ ] Jährliche Stichprobe Retention-Einhaltung
- [ ] Verweis in Datenschutzerklärung

---

## 6. Technische Referenzen

- `telemetry_client_contract` — keine PII in Pflichtfeldern
- `rougeaction_contract` — vor Persistenz auf Server
- Handoff Telemetrie/DiagNonstics (private Repos)

---

**Hinweis:** Konkrete Fristen sind Platzhalter bis Legal-Freigabe.
