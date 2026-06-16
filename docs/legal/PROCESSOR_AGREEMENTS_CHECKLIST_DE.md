# Auftragsverarbeitungsverträge (AVV/DPA) — Checkliste (DE)

**Stand:** 2026-06-16  
**Status:** Checkliste für Einkauf/Legal vor Beta mit Cloud-Diensten

Wenn Setuphelfer **personenbezogene Daten** über **Auftragsverarbeiter** verarbeitet (Hosting, E-Mail, Telemetrie-Infrastruktur, Billing), sind AVV gemärt Art. 28 DSGVO erforderlich.

---

## 1. Auftragsverarbeiter identifizieren

| Dienst | Zweck | Personenbezug? | AVV nötig? |
|--------|-------|----------------|------------|
| Cloud-Hosting (Telemetry/Diagnostics) | Server-Betrieb | Möglich (IP, IDs) | [ ] prüfen |
| E-Mail (SMTP) | Beta-Benachrichtigungen | E-Mail-Adressen | [ ] prüfen |
| Fehlertracking (falls eingeführt) | Crash-Reports | Möglich | [ ] prüfen |
| Payment/Billing | Abos | Ja | [ ] ja |
| CDN/Website | Marketing | Cookies/IP | [ ] prüfen |
| Backup-Cloud des **Kunden** | — | Verantwortlicher = Kunde | [ ] nein (Setuphelfer) |

---

## 2. Pflichtinhalte AVV (Art. 28 Abs. 3)

- [ ] Gegenstand und Dauer der Verarbeitung
- [ ] Art und Zweck der Verarbeitung
- [ ] Kategorien betroffener Personen und Datenarten
- [ ] Pflichten und Rechte des Verantwortlichen
- [ ] Weisungsgebundenheit
- [ ] Vertraulichkeit der Mitarbeiter
- [ ] TOM des Auftragsverarbeiters
- [ ] Unterauftragsverarbeiter (Liste + Genehmigung)
- [ ] Unterstützung bei Betroffenenrechten
- [ ] Löschung/Rückgabe nach Vertragsende
- [ ] Nachweise und Audits
- [ ] Meldung von Datenschutzverletzungen

---

## 3. Drittlandtransfer

- [ ] Speicherort EU/EWR oder Angemessenheitsbeschluss
- [ ] Sonst: SCC + TIA dokumentiert
- [ ] Keine US-Server ohne Legal-Freigabe in Public-Doku behaupten

---

## 4. Vor Vertragsschluss

- [ ] TOM des Anbieters eingeholt
- [ ] Subprocessor-Liste geprüft
- [ ] Datenminimierung im technischen Design (Contracts)

---

## 5. Laufende Pflege

- [ ] Jährliche Review Subprocessors
- [ ] Update bei neuem privatem Service (Operator, Telemetry)
- [ ] Dokumentation im Verzeichnis von Verarbeitungstätigkeiten

---

## 6. Verknüpfungen

- [`TOM_SECURITY_MEASURES_DRAFT_DE.md`](TOM_SECURITY_MEASURES_DRAFT_DE.md)
- [`DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`](DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md)
- [`TELEMETRY_CONSENT_REQUIRED_ITEMS_DE.md`](TELEMETRY_CONSENT_REQUIRED_ITEMS_DE.md)

---

**Hinweis:** Keine konkreten Anbieter-Namen in diesem Public-Entwurf — Liste intern pflegen.
