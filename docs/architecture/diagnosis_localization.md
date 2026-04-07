# Diagnose: Lokalisierung und kanonisches Schema (Phase 2)

**Stand:** Übergangsarchitektur im Repo umgesetzt (Backend + Frontend).  
**Nicht Ziel dieses Dokuments:** Vollständige Migration aller Regeln oder aller Sprachen außer DE/EN in der App.

---

## 1. Ist-Analyse (kurz, Dateibeleg)

| Komponente | Pfad |
|------------|------|
| API | `backend/api/routes/diagnosis.py` → `POST /api/diagnosis/interpret` |
| Interpreter | `backend/diagnosis/interpret_v1.py` |
| Pydantic-Modell | `backend/models/diagnosis.py` → `DiagnosisRecord` |
| Frontend-Typen | `frontend/src/types/diagnosis.ts` |
| Anzeige | `frontend/src/components/DiagnosisPanel.tsx` |
| API-Client | `frontend/src/api/diagnosisApi.ts` |
| Lokale Fallbacks | `frontend/src/diagnosis/localInterpretFallback.ts`, `localBackendDiagnosis.ts` |

**Vor Phase 2:** Nutzer sichtbare Texte (`title`, `user_message`, `suggested_actions`) wurden im Backend oft auf **Deutsch** erzeugt → EN-UI blieb deutsch.

---

## 2. Kanonisches Zielschema (DiagnosisRecord)

Zentrales Modell bleibt **ein** JSON-Objekt pro Antwort (`DiagnosisRecord`). Zusätzliche Felder (Pydantic, optional mit Defaults):

| Feld | Bedeutung |
|------|-----------|
| `schema_version` | `"1"` Legacy, `"2"` keyed + EN-Fallbacks in Legacy-Feldern |
| `localization_model` | `"legacy"` \| `"key_v1"` |
| `diagnosis_id` | Stabile ID (Punkt-Notation), Telemetrie |
| `diagnosis_code` | Bei `key_v1` i. d. R. = `diagnosis_id` |
| `module` | Modulkürzel (meist = `area`) |
| `event` | Auslöser, z. B. `event_type` der Anfrage |
| `severity`, `confidence`, `diagnose_type`, `companion_mode` | unverändert semantisch |
| `title_key`, `user_message_key` | i18n-Keys (Frontend: `de.json` / `en.json`) |
| `technical_summary_key` | optional; Roh-Text bleibt in `technical_summary` |
| `suggested_action_keys` | Liste i18n-Keys, Reihenfolge = UI |
| `title`, `user_message`, `suggested_actions` | **Legacy:** bei `key_v1` kurze **EN-Fallbacks** (wenn Key fehlt) |
| `technical_summary` | Rohauszug (Sprache der Quelle), nicht übersetzt |
| `docs_refs`, `faq_refs`, `kb_refs` | string-Pfade/IDs zu Doku (optional) |
| `evidence` | strukturiertes dict (optional) |
| `question_path` | optional, für geführte Diagnose später |
| `interpreter_version` | z. B. `v2` (Interpreter-Generation) |

**Benennung der i18n-Keys (verbindlich):**

```
diagnosis.codes.<area>.<slug>.title
diagnosis.codes.<area>.<slug>.user_summary
diagnosis.codes.<area>.<slug>.actions.<action_slug>
diagnosis.codes.<module>.shared.actions.<action_slug>   # geteilte Schritte
```

Beispiele:

- `diagnosis.codes.webserver.port_conflict.user_summary`
- `diagnosis.codes.system.backend_timeout.title`
- `diagnosis.codes.system.shared.actions.check_network`

---

## 3. Übergang alt → neu

| Aspekt | Regel |
|--------|--------|
| Erkennung | `localization_model === "key_v1"` → UI bevorzugt `*_key` via `t()` |
| Legacy | `localization_model === "legacy"` → UI nutzt `title` / `user_message` / `suggested_actions` wie bisher |
| Frontend | `DiagnosisPanel`: Keys mit Fallback auf parallele Legacy-Strings (Index bei Aktionen) |
| API | Alte Clients erhalten zusätzliche Felder; Pflichtfelder `title`/`user_message` bleiben gesetzt |
| Lokaler Fallback | `v1-local-fallback` / `v1-local`: gleiches `key_v1`-Muster wie Backend |

**Noch Legacy (exemplarisch Firewall):** `firewall.sudo_required`, `firewall.rule_apply_failed_port`, `firewall.rule_apply_failed_generic` — weiterhin `localization_model=legacy`, deutsche Freitexte, `schema_version=1`.

**Bereits `key_v1`:** `webserver.port_conflict`, `backup_restore.verify_failed_generic`, `system.backend_*`, `unknown.generic` (Fallback).

---

## 4. Lokalisierungsstrategie (Pflichtentscheidung)

- **Backend** liefert **keine** nutzerorientierten Übersetzungen mehr für neue Pfade — nur **Codes**, **Keys** (als Strings), **Severity**, **Roh-Technik** in `technical_summary`.
- **Frontend** (`react-i18next`) mappt Keys → DE/EN (und später weitere Locales).
- Begründung: Eine Quelle für UI-Sprache, konsistent mit App-i18n, testbare Keys, skalierbare Erweiterung pro Modul.

---

## 5. Diagnose-Matrix (Überblick)

| Diagnosefall | Modell | Frontend |
|--------------|--------|----------|
| Firewall Sudo / Port / Generic | legacy / Freitext | Legacy-Strings |
| Webserver Port-Konflikt | key_v1 | `diagnosis.codes.webserver.*` |
| Backup Verify failed | key_v1 | `diagnosis.codes.backup_restore.*` |
| System Backend unreachable | key_v1 | `diagnosis.codes.system.*` |
| Unknown fallback | key_v1 | `diagnosis.codes.unknown.*` |

**Offen:** Firewall-Regeln auf `key_v1` migrieren; weitere Module anbinden; optionale `technical_summary_key`-Templates.

---

## 6. FAQ / Wissensbasis

In diesem Schritt **keine** inhaltliche FAQ-/KB-Änderung: Nutzerfluss und sichtbare Texte bleiben über dieselben Keys in DE/EN abgedeckt wie zuvor (bzw. verbessert für EN). Verweise in `docs_refs` zeigen auf diese Datei und bestehende Architekturdocs.
