# Diagnose- und Companion-Architektur (Setuphelfer / piinstaller)

**Status:** Phase 1 umgesetzt (Grundmodell + Interpreter v1 + begrenzte UI).  
**Rahmen:** Backup & Restore bleibt Freigabe-Basis; Companion/Diagnose **ersetzt** keine Sicherheits- oder Restore-Prüfungen und **umgeht** sie nicht.

---

## 1. Ist-Analyse (Repository, knapp)

### 1.1 Event-, Debug-, Status- und Fehlermodelle

| Quelle | Inhalt |
|--------|--------|
| `backend/debug/logger.py` | JSONL-Events mit `run_id`, `request_id`, Typen (`STEP_*`, `APPLY_*`, `ERROR`, …). |
| `backend/debug/context.py` | `ContextVar` für `request_id` (Middleware setzt `X-Request-ID`). |
| `backend/models/events.py` | WebSocket `EventMessage`, Topics (`module.state.changed`, `job.progress`, …). |
| `backend/app.py` | Viele Routen: `{"status":"error","message":...}` bei HTTP 200 **oder** echte Statuscodes/`HTTPException`. Kein einheitliches API-Fehlerschema. |
| `backend/core/eventbus.py` | Publish an WS-Clients. |
| `storage/db.py` / Audit | `audit_log` für ausgewählte Ereignisse. |

### 1.2 Backend mit strukturierten Informationen

- `/api/system/status` inkl. Ampeln / `realtest_state` (Backup/Restore-Story).
- Security/Firewall: JSON mit `status`, `message`, teils `requires_sudo_password`.
- Webserver-Status-Endpunkte liefern strukturierte Dicts.
- Remote-API: Pydantic-Modelle unter `models/`, Session-Schutz.

### 1.3 Frontend: Fehler, Status, Hilfe

- `fetchApi` in `api.ts`: Timeout, keine zentrale Fehlernormalisierung.
- `toast.error` / `toast.success` verstreut (u. a. `BackupRestore.tsx`, `SecuritySetup.tsx`).
- `Dashboard.tsx`: Ampeln, Primäraktion, Backend-Fehlerkarte.
- `HelpTooltip`, `PandaHelper` (eher Motivation als technische Diagnose).
- `UIModeContext`: Modus `diagnose` (Navigation), keine gemeinsame Diagnose-Datenpipeline.

### 1.4 Wiederverwendbar für Diagnose-Interpretation

- `request_id` / JSONL für technische Korrelation (später).
- Bestehende API-Fehlerobjekte (`status`, `message`, Flags) als **Eingabe** für Interpreter.
- Ampel-/Status-API unverändert nutzbar; Companion **interpretiert**, nicht **neu bewertet** Restore/Backup.

### 1.5 Inkonsistenzen

- HTTP 200 mit logischem `status: error` vs. echte HTTP-Fehlercodes.
- Fehlertexte teils deutsch, teils englisch, teils hardcoded im Frontend.
- `debug/middleware.py` vs. Inline-Middleware in `app.py` (Duplikat, siehe `debug_flow.md`).
- Architekturdateien `TRANSFORMATIONSPLAN.md`, `UI_PLAN.md` u. a. können veraltete Zielbilder enthalten – diese Doku ist **ab jetzt** die Referenz für Diagnose/Companion, bis eine gezielte Bereinigung erfolgt.

### 1.6 Einordnung Phase 1

| Kategorie | Inhalt |
|-----------|--------|
| **Bereits vorhanden** | Debug-JSONL, Request-ID, WS-Events, gemischte API-Fehler, Dashboard-Status. |
| **Fehlend** (vor Phase 1) | Einheitliches Diagnose-Datenmodell, Interpreter-Schicht, Companion-UI-Muster. |
| **Riskant / inkonsistent** | Doppelte Fehlerstile; ohne Interpreter wiederholen Clients Logik. |
| **Phase 1 geeignet** | Backend erreichbar: Firewall-Regel-Fehler; Backend down: Dashboard-Kontext (lokaler Fallback). |

---

## 2. Zielarchitektur (Schichten)

### 2.1 Backend Event Layer

- Technische Ereignisse (Logs, API-Antworten, optional WS).
- Strukturierte Felder: `area`, `event_type`, `message`, `http_status`, `api_status`, `extra`.
- Korrelation über `request_id` / `run_id` wo vorhanden (Eingabe in `source_event` spiegeln).

### 2.2 Diagnose Layer

- **Klassifikation:** `diagnose_type`, `severity`, `confidence`.
- **Nutzerbotschaft:** `title`, `user_message` (Phase 1: deutsch aus Interpreter; i18n über `diagnosis_id` im Frontend möglich).
- **Technik:** `technical_summary` (kürbar, für „Details“).
- **Aktionen:** `suggested_actions[]`, `quick_fix_available` (nur wenn Aktion eindeutig und reversibel).
- **Stable ID:** `diagnosis_id` für Übersetzungen und Telemetrie-Später.

### 2.3 Companion Presentation Layer

- Tonalität: sachlich, nicht alarmistisch; Abstimmung mit Ampel (`companion_mode`).
- Modi: `info` | `caution` | `warning` | `blocked` | `recommendation` | `guided_step`.
- Tiefe: Anfänger Standardansicht; Experten aufklappbare technische Zusammenfassung.

### 2.4 UI Integration Layer

- Phase 1: `DiagnosisPanel` (Titel, Nachricht, Ampelfarbe, Liste „Nächste Schritte“, ausklappbare Technik).
- Einbindung: punktuell (Dashboard bei Backend aus, Security bei Firewall-Fehler).
- Später: Statuskarten, Inline „Was bedeutet das?“, Quick Actions nur mit Guardrails.

---

## 3. Companion-Regeln (verhaltensbezogen)

| Modus | Rolle |
|-------|--------|
| `info` | Erklären, keine Eile. |
| `caution` | Hinweis auf Risiko, keine Blockade. |
| `warning` | Handlung empfohlen, ggf. Daten gefährdet. |
| `blocked` | Weiterarbeit sinnlos bis Voraussetzung erfüllt (z. B. Sudo). |
| `recommendation` | Konkrete nächste Schritte ohne Hard-Block. |
| `guided_step` | Assistentenartig (später mit Wizard verknüpfbar). |

**Quick Action:** nur bei klarer, reversibler oder unkritischer Aktion; keine irreversiblen Systemeingriffe ohne vorherige Warnung (Phase 1: eher Links/Hinweise als neue Buttons).

---

## 4. Phase 1 (Umsetzung)

**Ziel:** Grundmodell + Interpreter **v1** (regelbasiert, gekapselt, erweiterbar) + 2 Integrationspunkte.

**Auswahl:**

1. **Dashboard – Backend nicht erreichbar** (Timeout/Verbindung/sonst): Nutzer sieht sofort **verständliche** Diagnose ohne API-Aufruf (**lokaler Fallback**, identische Semantik wie Backend-Regel `system.*` – in Doku vermerkt).
2. **Security – Firewall-Regel hinzufügen fehlgeschlagen:** typischer Nutzen, klare Fehlermeldungen von `ufw` (Port belegt, Regel existiert, Sudo).

**Nachziehen (klein):** `BackupRestore` – Fehler bei **`/api/backup/verify`** (Basic/Deep) lösen `POST /api/diagnosis/interpret` aus; Anzeige per `DiagnosisPanel` auf dem Backup-Tab (keine Quick Fixes, keine Backend-Änderung am Verify selbst).

**Webserver:** `WebServerSetup` – Fehler nach **`/api/webserver/configure`** mit Regel **`webserver.port_conflict`** (Port/Bind-Heuristik), Panel im Tab Konfiguration.

**Nicht in Phase 1:** Gesamtes System, alle Module, Bluetooth, Webserver-Port-Konflikte (Regeln können in v2 folgen). Cloud-Verify (`/api/backup/cloud/verify`) ist hier nicht angebunden.

**Interpreter v1:** Regeln in `backend/diagnosis/interpret_v1.py`, Konstante `INTERPRETER_VERSION = "v1"`. Kein „String-Matching als Endlösung“: Bedingungen pro Regel aus **Kombination** `area`, `event_type`, `api_status`, Teilstrings in `message`, optional `extra`.

---

## 5. API

- `POST /api/diagnosis/interpret`  
- Body: `DiagnosisInterpretRequest` (siehe `backend/models/diagnosis.py`).  
- Response: `DiagnosisRecord` (JSON-serialisierbar).  
- Kein Ersatz für Backup/Restore-Endpunkte; keine Änderung deren Verträge.

---

## 6. Erweiterbarkeit (Bluetooth, weitere Module)

- Neue **area**-Werte (z. B. `bluetooth`) und Regeln in neuer Datei `interpret_v2.py` oder angehängte Regelliste.  
- Gleiches `DiagnosisRecord`-Schema beibehalten oder versionieren über `schema_version`.

---

## 7. Nutzerperspektive (kurz)

**Was die Diagnosehilfe leistet:** Erklärt in einfacher Sprache, was vermutlich schiefgelaufen ist, und schlägt **sinnvolle nächste Schritte** vor. Technische Details sind optional sichtbar.

**Was sie nicht leistet:** Kein Ersatz für Logs oder Support-Bundle; keine Garantie für die Ursache; **keine** Aufhebung von Sicherheitsbeschränkungen von Backup/Restore.

---

## 8. Entwicklerperspektive (kurz)

**Neue Diagnose hinzufügen:**

1. In `interpret_v1.py` eine neue Regelfunktion mit eindeutiger Bedingung und Rückgabe `DiagnosisRecord`.  
2. Regel in `RULES_V1` eintragen (Reihenfolge = Priorität, erste Treffer gewinnt).  
3. pytest in `tests/test_diagnosis_interpreter_v1.py` ergänzen.  
4. Optional: Frontend-i18n unter `diagnosis.*` und `diagnosis_id` nutzen.

**Companion-UI:** Komponente `DiagnosisPanel`; Props siehe Frontend-Quelltext.

---

## 9. Abgleich Dokumentation / Repo

| Thema | Vorschlag |
|-------|-----------|
| Alte UI-/Transformationspläne | Nicht automatisch löschen; bei nächster Doku-Runde mit dieser Datei abgleichen oder verweisen. |
| `debug_flow.md` | Ergänzung: Diagnose-API nutzt dieselbe `request_id`-Semantik für `source_event` (optional im Request mitschicken). |

---

*Letzte inhaltliche Ausrichtung: Phase 1 Companion/Diagnose ohne Bluetooth.*
