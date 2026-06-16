# Telemetrie-Einwilligung — Erforderliche Inhalte (DE)

**Stand:** 2026-06-16  
**Technische Basis:** `backend/core/telemetry_client_contract.py`, `redaction_contract.py`

Checkliste für **informierte Einwilligung** vor aktivem Telemetrie-Versand (Opt-in).

---

## 1. Transparenz (vor Aktivierung)

- [ ] Klare Bezeichnung „optionale Nutzungs-/Diagnosedaten“
- [ ] Auflistung der `TelemetryDataCategory`-Kategorien in verständlicher Sprache:
  - Version
  - Runtime-Health
  - Fehler-Zusammenfassungen
  - Hardware-Klasse (keine Seriennummern im Klartext)
  - Rescue-Session-Metadaten (falls aktiviert)
- [ ] Hinweis: **kein** Send bei `opt_in_state: disabled`
- [ ] Ziel: verbesserte Stabilität — **keine** Werbung ohne separate Einwilligung

---

## 2. Redaction und Vorschau

- [ ] Nutzer sieht **redigierte Vorschau** vor erstem Send (`local_preview_ok`)
- [ ] Erklärung der Redaction-Kategorien (IP, E-Mail, Pfade, Tokens — siehe `redaction_contract`)
- [ ] Kein Send wenn `redaction_applied: false`

---

## 3. Widerruf

- [ ] Telemetrie jederzeit deaktivierbar in Einstellungen
- [ ] Wirkung: künftige Sends gestoppt (`opt_in_state: disabled`)
- [ ] Hinweis auf bereits übertragene Daten und Löschfristen (`DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`)

---

## 4. Rechtsgrundlage (mit DPO klären)

- [ ] Art. 6 Abs. 1 lit. a DSGVO (Einwilligung) oder andere Rechtsgrundlage dokumentiert
- [ ] Separate Einwilligung von AGB, falls erforderlich
- [ ] Keine vorangekreuzte Checkbox

---

## 5. Auftragsverarbeitung

- [ ] Wenn Server durch Drittanbieter gehostet: AVV (`PROCESSOR_AGREEMENTS_CHECKLIST_DE.md`)
- [ ] Speicherort/Region benannt (ohne interne Hostnamen in Public-Doku)

---

## 6. Minderjährige / B2B

- [ ] B2B: Verantwortlicher ist IT-Admin des Kunden
- [ ] Kein Tracking zu Marketingzwecken ohne zusätzliche Consent-Ebene

---

## 7. UI-/Copy-Anforderungen

- [ ] Kurzfassung + Link zur vollständigen Datenschutzerklärung
- [ ] Beispiel-Endpunkt nur als Platzhalter in Entwicklerdoku (`*.setuphelfer.example`)
- [ ] Keine echten internen URLs in öffentlichen Screenshots

---

## 8. Technische Prüfung vor Go-Live

- [ ] `validate_client_envelope()` ohne Fehler bei aktiviertem Opt-in
- [ ] Unit-Tests `test_telemetry_client_contract_v1.py` grün
- [ ] Boundary-Gate: keine Server-Secrets im Client-Build
