# Developer Backend Watchdog — Deploy Order Fix

**Datum:** 2026-06-03

## Ist-Analyse (`scripts/deploy-to-opt.sh`)

| Anforderung | Vorher | Nachher |
|-------------|--------|---------|
| `daemon-reload` vor Restart | **yes** (Zeile 268 vor restart) | **yes** (unverändert, dokumentiert) |
| Retry `/api/version` | 10×1s, Exit 0 bei Fehler | **15×2s**, Exit **1** bei Fehler |
| Fehlermeldung + journal-Hinweis | warn only | **err** + journalctl-Hinweis |
| `wait_for_backend_api \|\| exit 1` | nein | **yes** |

## Ursache historischer Ausfälle

Deploy schrieb Units/Drop-ins; wenn Operator **ohne** `daemon-reload` neu startete oder sofort `curl` ausführte, entstand transient `backend_not_listening` (siehe `BACKEND_DOWN_AFTER_RELEASE_RESTART_RESULT.md`).

## Pflichtbewertung

| Feld | Wert |
|------|------|
| daemon-reload vor Restart vorhanden | **yes** |
| Retry auf /api/version vorhanden | **yes** (gehärtet) |
| Fehlerklasse bei Port 8000 down | **yes** (non-zero exit) |
| **Status** | **fixed** |
