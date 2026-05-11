# Backup/Restore – Real-Tests und API-Nachweis

Dieses Dokument unterliegt der **Wahrheitspflicht** (`120_DOCUMENTATION_TRUTH_RULES.md`).

---

## Umgebung (Stand: Ausführung in dieser Session)

| Aspekt | Befund |
|--------|--------|
| **Host-Python** (`/usr/bin/python3`) | **FastAPI nicht importierbar** – keine Backend-Abhängigkeiten im System-Python. |
| **Lokales `venv` im Repo** | **Nicht vorhanden.** |
| **API-Tests ausführbar** | **Ja**, über **Docker**: Image `piinstaller-backend-test:latest` (Repo-`Dockerfile`), Container mit Bind-Mounts für `/tmp/setuphelfer-test` und `/tmp/setuphelfer-restore-test`, Port `127.0.0.1:18000:8000`. **Kein pip/apt auf dem Host** für diese Nachweise. |
| **Minimaler Weg ohne Docker** (nur Vorschlag, nicht automatisch ausgeführt) | `python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt`, dann `TestClient` oder `uvicorn` – erfordert ausdrückliche Freigabe für Paketinstallation. |

---

## 1. Real ausgeführte API-Tests (Docker + curl)

**Methode:** `curl -sS -X POST http://127.0.0.1:18000/...` mit JSON-Body, Antworten mit `python3 -m json.tool` geprüft.  
**Image:** nach Änderungen an `backend/app.py` neu gebaut (`docker build -t piinstaller-backend-test:latest -f Dockerfile .`).

### POST `/api/backup/verify`

| # | `backup_file` | Erwartung (kurz) | `api_status` / Kernfelder | Ergebnis |
|---|---------------|------------------|---------------------------|----------|
| 1 | `.../valid-backup.tar.gz` | ok, valid | `ok`, `results.valid: true`, `file_count: 4` | **bestanden** |
| 2 | `.../corrupt-not-gzip.tar.gz` | Fehler, kein gültiges gzip | `error`, `data.results.valid: false` | **bestanden** |
| 3 | `/etc/hosts` | Allowlist | `error`, `data.results.valid: false` | **bestanden** |
| 4 | `evil-traversal.tar.gz` | gesperrt | `error`, `blocked_entries`, `results.valid: false` | **bestanden** |
| 5 | `evil-absolute.tar.gz` | gesperrt | wie oben | **bestanden** |
| 6 | `evil-symlink.tar.gz` | gesperrt | wie oben | **bestanden** |
| 7 | `evil-hardlink.tar.gz` | gesperrt | wie oben | **bestanden** |
| 8 | `evil-fifo.tar.gz` | gesperrt | wie oben | **bestanden** |

**Hinweis:** `realtest_state.last_verify_ok` spiegelt den **letzten** Verify-Aufruf wider. Für eine grüne Backup-Ampel nach Security-Tests mit Evil-Archiven danach erneut ein **gültiges** Archiv verifizieren.

### POST `/api/backup/restore`

| # | Modus | `backup_file` | Erwartung | Ergebnis |
|---|--------|---------------|-----------|----------|
| 1 | `dry-run` | `valid-backup.tar.gz` | `api_status: ok`, `data.analysis`, kein Schreiben | **bestanden** |
| 2 | `preview` | `valid-backup.tar.gz` | `api_status: ok`, `preview_dir` unter `/tmp/setuphelfer-restore-test/<ts>/` | **bestanden** |
| 3 | `dry-run` | `/etc/passwd` | Allowlist-Fehler | **bestanden** |
| 4 | `preview` | `evil-symlink.tar.gz` | blockiert, `data.analysis.blocked_entries` | **bestanden** |

**Host-Prüfung nach Preview:** Datei `.../restore-root/hello.txt` mit Inhalt `setuphelfer-realtest-ok` vorhanden (**real**).

### GET `/api/system/status`

| Prüfpunkt | Befund |
|-----------|--------|
| `realtest_state` in `data` und top-level | **ja** |
| Ampel nach erfolgreichem Verify + Preview | `backup: green`, `restore: green` (wenn zuletzt gültiger Verify und erfolgreicher Preview; siehe Reihenfolge oben) |
| Blockierter Restore überschreibt **nicht** mehr `last_preview_ok` | **ja** (Fix: gesperrte Archive setzen kein `last_preview_ok: false`) |

---

## 2. Real ausgeführte OS-Level-Tests (ohne HTTP)

- **`tar -tzf`** auf gültigen/korrupten Archiven (frühere Session / Skript `setuphelfer/create_backup_realtest_data.py`).
- **Manuelles Entpacken** und **Python-`tarfile`**-Inspektion der Evil-Archive (Member-Typen).

---

## 3. Was weiterhin nicht (oder nur eingeschränkt) API-getestet wurde

| Bereich | Grund |
|---------|--------|
| **Verschlüsselte Backups**, Verify `mode: deep` | Kein Testschlüssel / kein GPG-Flow in dieser Laufumgebung. |
| **Sehr große Archive** (>100 Einträge) | Kein künstliches Riesenarchiv erzeugt; Performance nicht gemessen. |
| **Parallele Clients** / Last | Nicht geprüft. |
| **Host ohne Docker** | Kein FastAPI auf dem System-Python → keine direkten TestClient-Läufe dort. |

---

## 4. API-Contract (status, api_status, message, data)

**Anpassungen in dieser Phase:**

- Verify bei **nicht lesbarem** `.tar.gz`: `data.results` mit `valid`, `file`, `error`, `verification_mode`.
- Verify bei **Allowlist-Verstoß** und **Datei fehlt**: `data.results` ergänzt.
- Restore bei **Analysefehler**: `data.analysis_error` (kurzer Text).

**Bekannte Eigenheiten (bewusst klein gehalten):**

- Erfolgreiche Verify-/Restore-Antworten duplizieren teils Felder in `data` und top-level (`results`, `preview_dir`) – kompatibel zum bestehenden Frontend; kein großes Refactor.
- `status` ist bei FastAPI-Routen oft HTTP-„Erfolg“ (`200`), fachlicher Zustand steht in `api_status`.

---

## 5. Preview-Cleanup

- Nach **erfolgreichem** API-Preview ruft das Backend `_cleanup_old_preview_dirs(preview_dir)` auf.
- **TTL:** `PREVIEW_SANDBOX_TTL_SECONDS = 86400` (24 h): ältere Zeitstempel-Verzeichnisse unter `/tmp/setuphelfer-restore-test/` werden entfernt, das **aktuelle** `preview_dir` bleibt.
- Verzeichnisse **jünger als 24 h** bleiben liegen (mehrere Durchläufe sichtbar; kein sofortiges Löschen der vorherigen Runs).
- Manuell angelegte Ordner (z. B. `manual-preview`) werden nur entfernt, wenn sie unter derselben Basis liegen **und** die TTL überschreiten.

---

## 6. Verify: `head -100` und Zählung

- Für **unverschlüsselte** `.tar.gz` nach bestandener Member-Analyse: **`file_count`** kommt aus der **vollständigen** `tarfile`-Analyse (`total_files + total_dirs + total_other`), **nicht** aus `head -100` / `wc -l`.
- **`sample_files`** stammen weiterhin aus der ersten `tar -tzf | head -100`-Ausgabe: bei Archiven mit **mehr als 100 Einträgen** ist die Stichprobe unvollständig, die **Validität** des Archivs wird aber nicht allein davon abgeleitet.
- **Bewertung:** Für Integritäts-Go/No-Go und Sicherheits-Blocklisten ist das **vertretbar**; eine vollständige Namensliste großer Archive wäre ein separates Feature (bewusst nicht umgesetzt).

---

## 7. Testdaten – Erzeugung

```bash
python3 setuphelfer/create_backup_realtest_data.py
```

Zielverzeichnis: `/tmp/setuphelfer-test/` (siehe Skriptkommentare).

---

## 8. Offene Risiken

- Produktionspfade und Berechtigungen können von der Docker-Sandbox abweichen.
- TTL-Cleanup löscht nicht sofort alle Zwischenstände; `/tmp` kann je nach System geleert werden.
- Ohne erneutes Verify eines **produktiven** Pfads nach Tests bleibt `last_verify_ok` ggf. auf einem negativen Ergebnis.

---

## 9. Freigabebewertung

**Freigabefähig** für den Nachweis: Backup/Restore-**API** inkl. Verify, Restore (Dry-Run/Preview), Systemstatus und Security-Blocklisten – **nachgewiesen per Docker-HTTP-Tests** wie oben.

**Eingeschränkt:** Verschlüsselung/Deep-Verify, Riesenarchive, reiner Host ohne Container/venv.

**Nicht freigabefähig:** Root-Restore (weiterhin gesperrt, Feature-Gatekeeping).
