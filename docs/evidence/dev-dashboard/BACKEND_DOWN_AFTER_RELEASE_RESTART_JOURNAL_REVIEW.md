# Backend Down After Release Restart — Journal Review (Phase 1)

**Datum:** 2026-06-03  
**Log:** `backend_down_after_release_restart_backend_journal_latest.log`

## Journal-Zugriff

| Quelle | Ergebnis |
|--------|----------|
| `journalctl` (ohne sudo) | **Keine Einträge** (Gruppe `adm`/`systemd-journal` fehlt für Agent) |
| `journalctl` (sudo) | **blocked** (Passwort erforderlich) |

## ERROR-Extract (Agent-Session)

Keine journal-Zeilen verfügbar. Korrelierende Belege:

1. **Terminal 6:** Deploy-Ende → `curl (7)` Port 8000; systemd `daemon-reload` Warnung.
2. **Terminal 6:** Nach `daemon-reload` + `restart` → erneut `curl (7)` (sofortiger Probe).
3. **Phase 0 (später):** Service **active**, uvicorn auf `:8000`, `/api/version` 200, `install_profile=release`.

## Pflichtbewertung

| Feld | Wert |
|------|------|
| Konkreter Fehler aus Journal | **nicht lesbar** (Zugriff); indirekt: Unit-Änderung ohne Reload + Restart-Fenster |
| Importfehler | **no** |
| Unit-/ExecStart-Fehler | **no** (ExecStart läuft: uvicorn `app:app` :8000) |
| Port-Konflikt | **no** |
| Permission-Fehler | **no** |
| Profil-/Environment-Fehler | **no** |
| Service startet und beendet sich | **no** (stable active) |
| **Status** | **`systemd_reload_required`** (primär); sekundär transient `service_crash`/`backend_not_listening` während Restart — **nicht** `import_failure` |
