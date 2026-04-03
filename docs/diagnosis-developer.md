# Diagnose-API & Interpreter – Kurz für Entwickler

## Endpunkt

`POST /api/diagnosis/interpret`  
Body: `DiagnosisInterpretRequest` (siehe `backend/models/diagnosis.py`).  
Response: `DiagnosisRecord` (JSON, `schema_version` + `interpreter_version`).

## Neuen Treffer hinzufügen

1. In `backend/diagnosis/interpret_v1.py` eine Funktion `def _rule_...(req) -> Optional[DiagnosisRecord]`.
2. Eintrag in `RULES_V1` an passender Prioritätsstelle (erste Regel mit Treffer gewinnt).
3. Tests in `backend/tests/test_diagnosis_interpreter_v1.py`.
4. Frontend: optional `DiagnosisPanel` anbinden; Texte kommen aus dem Record oder i18n.

## Versionierung

- Große Änderungen: neue Datei `interpret_v2.py`, `INTERPRETER_VERSION` anpassen.
- Schema-Bruch: `schema_version` in `DiagnosisRecord` erhöhen und Frontend-Typen anpassen.

## Companion-UI

Komponente: `frontend/src/components/DiagnosisPanel.tsx`  
Typen: `frontend/src/types/diagnosis.ts`  
Client: `frontend/src/api/diagnosisApi.ts`

## Webserver (Konfiguration)

Bei Fehler von `POST /api/webserver/configure` (Seite **Webserver → Konfiguration**) sendet `WebServerSetup.tsx` `area: webserver`, `event_type: configure_failed` und die Servermeldung. Trifft die Heuristik zu, liefert der Interpreter **`webserver.port_conflict`** (kein Quick Fix).

**Erkannte Muster (v1, Auszug):** u. a. `address already in use`, `EADDRINUSE`, `already in use`, `could not bind`, `:80` / `:443`, `port 80` / `port 443`, `98: address`, deutsch z. B. Port/belegt/Adresse … verwendung.

**Grenzen:** Andere Configure-Fehler (PHP-Install, apt, allgemeine Exceptions ohne Port-Hinweis) fallen auf **`unknown.generic`**. Preset-Weg (`PresetsSetup` → `/api/webserver/configure`) ist hier **nicht** angebunden.

## Backup / Restore (Verify)

Bei fehlgeschlagener **lokaler** Prüfung (`POST /api/backup/verify`, Basic oder Deep) ruft `BackupRestore.tsx` `POST /api/diagnosis/interpret` mit `area: backup_restore`, `event_type: verify_failed` und der Roh-/Fehlermeldung auf. Es gibt **keine** Quick-Fix-Buttons und keine Änderung der Verify-Backendlogik.

## Offline-Fall

Wenn das Backend nicht erreichbar ist, kann kein `POST /interpret` ausgeführt werden. Dashboard nutzt `localBackendDiagnosis()` – Semantik muss mit `_rule_system_backend_unreachable` übereinstimmen (siehe `docs/architecture/diagnose_companion.md`). **Hinweis:** Schlägt Verify fehl, während der Diagnose-Endpunkt nicht erreichbar ist, bleibt das Panel leer (`postDiagnosisInterpret` liefert `null`) – Toasts und bestehende UI bleiben bestehen.
