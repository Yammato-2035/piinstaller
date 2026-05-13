# Backup Package Activity Preflight — Spezifikation (DE)

**Status:** Entwurf (Design-Phase, keine Produktimplementierung in diesem Schritt)  
**Auslöser:** BR-001 Job `e341a326ac69` — Abbruch **`backup.blocked_package_activity`**, **`UPDATE-CONFLICT-041`**, Laufzeit-Kollision mit **`apt-get autoremove --purge -y`** / **`mintupdate-automation-autoremove.timer`**. Siehe Evidence **`docs/evidence/backup-restore/BR-001_package_activity_failure_2026-05-13.md`**.

**Ziel:** Vor (und optional ergänzend zu) langen Full-Backups ein **geführtes Backup-Fenster** herstellen: Betreiber sieht **konkrete** Blocker (Prozesse, Locks, `dpkg --audit`, Timer), kann **warten**, **Anwendungen schließen** oder **zeitlich begrenzt** Automatisierung pausieren — **ohne** dauerhafte Deaktivierung von Diensten.

---

## 1. Ist-Analyse (Produktcode, Stand Entwurf)

### 1.1 Backend (`backend/app.py`)

| Ort | Verhalten |
|-----|-------------|
| **`POST /api/backup/create`** | Vor Job-Start: **`_detect_active_package_operations()`**. Bei Treffer: Response **`backup.blocked_package_activity`**, **`diagnosis_id`: `UPDATE-CONFLICT-041`**, Liste **`active_package_processes`** (max. 10). |
| **`_do_backup_logic` → `_run_tar`** (synchroner Tar-Pfad) | Während **`tar`**: alle **0,5 s** erneute Prozess-Erkennung; bei Treffer: **`SIGTERM`**/`SIGKILL` an Prozessgruppe, Rückgabe mit **`active_package_processes`**, u. a. **`returncode` -16**. |

**Erkennungslogik `_detect_active_package_operations` (vereinfacht):**

- Ignoriert: **`/usr/lib/apt/methods/`** (Transport), **`unattended-upgrade-shutdown`** (Wartefähigkeit, explizit ausgenommen).
- Blockiert, wenn in **`name` + cmdline`** (Kleinbuchstaben) u. a. vorkommt: **` apt-get `**, **` apt `**, **` dpkg `**, **`unattended-upgrade`**, **`apt.systemd.daily`**, oder **`name`** ∈ `{apt, apt-get, dpkg, apt.systemd.daily}`.

**Lücken:** Keine explizite Erkennung von **PackageKit**, **mintUpdate** (GUI), **update-manager**; keine **Lock-Datei**-Prüfung; kein **`dpkg --audit`**; keine **systemd-Timer**-Abfrage.

### 1.2 Runner (`backend/tools/backup_runner.py`)

| Ort | Verhalten |
|-----|-------------|
| **`_run_tar_pipeline_from_preflight`** | **Vor** `systemd-inhibit` und Tar: **`_detect_active_package_operations()`** — bei Treffer: **`status.json`** mit **`code`:** `backup.blocked_package_activity`, **`abort_reason`:** `package_activity_detected_preflight`. |
| **Monitor-Schleife während Tar** | Alle **0,5 s**: erneute Erkennung; bei Treffer: Kindprozess beenden, **`abort_reason`:** `package_activity_detected_runtime` (wie Job `e341a326ac69`). |

Die Funktion **`_detect_active_package_operations`** ist im Runner **dupliziert** (gleiche Heuristik wie im Backend); bei Änderungen der Preflight-Spezifikation ist **Konsolidierung** (ein Modul, zwei Aufrufer) langfristig sinnvoll.

---

## 2. Produktmangel

1. **Zu spätes oder unvollständiges Gate:** API blockiert nur bekannte Prozessmuster; **GUI-Updater** (z. B. MintUpdate) und **Timer-geförderte** `apt-get`-Aufrufe können **während** eines bereits gestarteten langen Backups beginnen → teurer Abbruch nach vielen Minuten Laufzeit.
2. **Keine strukturierte Betreiberführung:** Kein dedizierter Schritt „Preflight-Report“ mit Locks, `dpkg --audit`, nächsten Timer-Feuern.
3. **Keine Wiederherstellungs-Erinnerung:** Nach manuellem `systemctl stop …timer` (Betreiber) muss die UI/Doku explizit an **`start`** erinnern (kein `disable`).

---

## 3. Zielbild: „Backup Package Activity Preflight“

### 3.1 Überblick

- **Option A (API-first):** Neuer Endpunkt z. B. **`GET /api/backup/package-preflight`** oder **`POST`** mit leerem/minimalem Body — liefert **nur Diagnose**, startet **kein** Backup.
- **Option B (UI-first):** Gleiche Datenstruktur; UI ruft vor **`POST /api/backup/create`** auf und zeigt Checkliste + Aktionen.

Empfehlung: **A + B** — API für Automatisierung und Tests, UI für Menschen.

### 3.2 Erkennung aktiver Prozesse (Pflicht-Erweiterung)

Erweiterte Menge (Namen **oder** `cmdline`, case-insensitive), konservativ blockierend wenn **tatsächlich** Paketoperation ausführend (Heuristiken dokumentieren):

| Kategorie | Beispiele |
|-----------|------------|
| APT | `apt`, `apt-get` |
| dpkg | `dpkg`, `dpkg-deb`, `dpkg-reconfigure` |
| Unattended | `unattended-upgrade` (weiterhin Shutdown-Helper explizit ausnehmen, sofern kein Lock) |
| Desktop | `packagekitd`, `mintupdate`, `mintUpdate`, `update-manager` |

**Hinweis:** Abgrenzung zu **Idle-DAEMONs** (nur im Speicher, kein Lock): Spezifikation soll **zweistufig** sein: (1) Prozessliste, (2) optional Lock/`fuser` — Block nur bei **Prozess + Lock** oder bei **bekannt riskanter cmdline** (Konfiguration).

### 3.3 Lock-Prüfung (Pflicht)

Pfad-Liste (Linux üblich):

- `/var/lib/dpkg/lock`
- `/var/lib/dpkg/lock-frontend`
- `/var/lib/apt/lists/lock`
- `/var/cache/apt/archives/lock`

Auswertung: **`fuser`** oder gleichwertig (nur wenn privilegiert ausführbar — Rückgabefeld **`lock_check_skipped_reason`** wenn nicht).

### 3.4 `dpkg --audit` (Pflicht)

- Ausführung nur mit passenden Rechten.
- Ergebnis: **`ok`** | **`broken_packages`** | **`skipped_no_sudo`**.
- Bei **`broken_packages`:** Preflight **`warn`** oder **`block`** (Policy-Flag im Request oder Server-Default).

### 3.5 Timer-Erkennung (Informationspflicht)

Mindestens **Status + Next** (read-only) für:

- `apt-daily.timer`
- `apt-daily-upgrade.timer`
- `mintupdate-automation-upgrade.timer`
- `mintupdate-automation-autoremove.timer`
- `dpkg-db-backup.timer`
- `apt-show-versions.timer`

Antwortstruktur: Liste von `{ "unit": "…", "active_state": "…", "next_elapse": "…" }`. **Kein** automatisches `stop` durch Setuphelfer in v1 ohne explizite Benutzerbestätigung (siehe 3.6).

### 3.6 Benutzerführung

| Aktion | Beschreibung |
|--------|----------------|
| **Warten** | Countdown / „Nächster Timer in …“; erneuter Preflight-Button. |
| **Schließen** | Hinweis: MintUpdate / Softwareverwaltung beenden. |
| **Temporär pausieren** | Nur nach **explizitem Opt-in** (z. B. Checkbox + Bestätigung): `systemctl stop <timer>` — **niemals** `disable`. Nach Backup: **prominent** „Timer wiederherstellen“ → `systemctl start <timer>`. |

### 3.7 Wiederherstellung nach Backup

- Wenn Setuphelfer (oder Helper) Timer gestoppt hat: **Pflicht**-Schritt im Job-Abschluss (success **und** error): Timer wieder **`start`**, Ergebnis in **`status.json`** / Evidence protokollieren.
- Wenn Betreiber manuell pausiert hat: UI-Hinweis aus Runbook **`BR-001_package_activity_retry_runbook_2026-05-13.md`**.

### 3.8 Fehlercodes und i18n (Vorschlag)

| Code | Nutzung | DE (Kurztext) | EN (Kurztext) |
|------|---------|---------------|---------------|
| `backup.package_preflight_ok` | Alle kritischen Checks grün | Paketumgebung für Backup geprüft, kein Blocker. | Package environment clear for backup. |
| `backup.package_preflight_blocked` | Blocker vorhanden | Backup derzeit nicht empfohlen: siehe `blockers`. | Backup not recommended: see `blockers`. |
| `backup.package_preflight_warn` | Nur Warnungen | Backup möglich, Risiken siehe `warnings`. | Backup possible; see `warnings`. |
| `backup.package_preflight_unavailable` | z. B. kein sudo für Locks | Teilprüfungen übersprungen (`skipped_checks`). | Some checks skipped (`skipped_checks`). |

Bestehende Codes bleiben für **harten** Abbruch: **`backup.blocked_package_activity`** (`UPDATE-CONFLICT-041`), **`package_activity_detected_preflight`** / **`_runtime`** im Runner.

**i18n:** Keys unter z. B. `backup.package_preflight.*` in bestehenden Locale-Dateien; UI zeigt strukturierte Liste (`blockers[].i18n_key`, `blockers[].detail`).

### 3.9 Evidence-Felder (JSON)

Vorschlag für Preflight-Response und/oder `BR-001.json`-Anbindung:

```json
{
  "preflight_version": 1,
  "checked_at": "ISO-8601",
  "process_scan": { "blocking": [], "ignored": [] },
  "locks": { "paths": [], "holders": [] },
  "dpkg_audit": { "status": "ok|broken|skipped", "stdout_excerpt": "" },
  "timers": [],
  "recommendation": "proceed|wait|abort",
  "timer_pause_applied": false,
  "timer_restore_required": false
}
```

---

## 4. Tests (geplant, keine Implementierung in diesem Prompt)

| ID | Beschreibung |
|----|----------------|
| **BR-011** | Matrixzeile „Package Activity Preflight“ — API liefert Struktur; blockiert bei simuliertem `apt-get`; Locks optional gemockt. |
| **Unit** | Konsolidierte Erkennungsfunktion: Positive/Negative Fälle (apt methods, shutdown-helper). |
| **Integration** | `GET`/`POST` Preflight gegen laufendes Backend (Dev). |

---

## 5. Verweise

- EN: **`BACKUP_PACKAGE_ACTIVITY_PREFLIGHT_EN.md`**
- Knowledge-Base: **`docs/knowledge-base/backup/BACKUP_PACKAGE_ACTIVITY_PREFLIGHT.md`**
- Runbook: **`docs/evidence/backup-restore/BR-001_package_activity_retry_runbook_2026-05-13.md`**
