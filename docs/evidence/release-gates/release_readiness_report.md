# Release Readiness – Bericht

**Generiert:** 2026-05-13 (STRICT — Voll-Deploy/Version-Fix, Agent ohne TTY-`sudo`)  
**Gesamtstatus:** `blocked`

## Kurzfassung

**GitHub Actions `ci.yml`:** Run **25751304968** — **success** (HEAD `55d7cec`). **BR-001:** **blocked**. Produktiv: **`GET /api/version` → HTTP 500** — Ursache dokumentiert: **`/opt/setuphelfer/config/version.json`** hat noch das **Legacy-Schema** (`version`/`codename`/`release_date`), **`core.versioning`** erwartet **`version_source_of_truth": true`**. Die fünf Backend-Dateien **`app.py`**, **`safe_device.py`**, **`versioning.py`**, **`registry.py`**, **`matcher.py`** sind unter **`/opt`** per **SHA256 identisch** zum Workspace; ausstehend ist primär **`config/version.json`** + **`systemctl restart`** ( **`sudo`** im Agent **BLOCKED** ). **`target-check`** ausschließlich **`/media/gabriel/setuphelfer-back`:** **HTTP 200**, JSON **`backup.backup_target_not_writable`** (Schreibtest EROFS); Shell-**`findmnt`** zeigt **`rw`** — Widerspruch in **`BR-001_readonly_target_and_api500_analysis_2026-05-12.md`**. Evidence-Hauptdatei: **`BR-001_backend_update_and_version_fix_2026-05-13.md`**. **Kein** Backup-Start.

## Ampelüberblick

| Bereich | Status |
|---------|--------|
| Backup/Restore/Verify (Evidence) | Rot (BR-001 **blocked** — `/opt`-Deploy vom Operator auf Host ausstehend) |
| Hardware | Rot |
| Rescue Stick real | Rot |
| CI-Nachweis aktuell | **Grün** (GitHub `ci.yml` Run **25751304968** success, HEAD 55d7cec) — Release gesamt wegen BR-001 weiter `blocked` |
| Website live vs. Markdown | Rot |
| Affiliate | Gelb (Policies) |
| Legal | Rot |
| P0-Blocker | vorhanden (fehlende E2E-Evidence) |

## Empfehlung

**Nicht starten** bis mindestens ein dokumentierter Backup→Verify→Restore→Boot→Service-Zyklus auf freigegebenem Medium und aktuelle CI-Logs als Evidence vorliegen.

## Nächste Schritte

Siehe `STATUS_MATRIX.md` und Abschlussbericht der letzten Master-Prompt-Ausführung.
