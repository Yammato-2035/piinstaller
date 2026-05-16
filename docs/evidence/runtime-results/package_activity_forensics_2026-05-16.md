# Package Activity Forensics — UPDATE-CONFLICT-041 (2026-05-16)

**Modus:** STRICT, read-only während aktiver BR-001-Läufe. Kein Backup-Abbruch, kein apt install/upgrade, keine Timer-Deaktivierung in diesem Dokument.

**Betroffene Jobs:**

| job_id | Ergebnis | Ziel | Ende (UTC) |
|--------|----------|------|------------|
| `e0bba3dff5e5` | `backup.blocked_package_activity` | `/media/setuphelfer/br001` | `2026-05-16T15:23:48Z` |
| `927469d42503` | `running` (Forensik-Snapshot) | `/media/setuphelfer/br001` | — |

---

## Phase 0 — Runtime Gate

| Prüfung | Ergebnis |
|---------|----------|
| `./scripts/check-runtime-deploy-gate.sh` | **Exit 0** — „OK (Version, Pfad, deploy_drift/Manifest)“ |
| `/api/version` HTTP 200 | ja — `project_version` **1.7.1**, `backend_runtime_path` **/opt/setuphelfer/backend** |
| Workspace `config/version.json` | **1.7.1** (Match) |
| `setuphelfer-backend.service` | aktiv (Gate-Skript) |

**Dashboard (bestätigt):** `deploy_drift.status` = **green**, `manifest_match` = **true**, `safe_test_mode.mode` = **UNLOCKED** (`jq '.dashboard | {deploy_drift: .deploy_drift.status, safe_test_mode: .safe_test_mode.mode}'` auf `/api/dev-dashboard/status`).

---

## Phase 1 — Job `e0bba3dff5e5` (fehlgeschlagen)

### status.json (Kern)

- **status:** `error`
- **code:** `backup.blocked_package_activity`
- **diagnosis_id:** `UPDATE-CONFLICT-041`
- **abort_reason:** `package_activity_detected_runtime`
- **backup_started_at:** `2026-05-16T13:57:10Z` (~15:57 CEST)
- **backup_finished_at:** `2026-05-16T15:23:48Z` (~17:24 CEST)
- **Laufzeit:** ~5197 s (~1h 27min)
- **bytes_current (bei Abbruch):** 123505737728 (~115 GiB)
- **archive_path (geplant):** `/media/setuphelfer/br001/pi-backup-full-20260516_155710.tar.gz`
- **partial_deleted:** `true`
- **subprocess_returncode:** `-15`

### Erfasste Paketprozesse (Runtime-Snapshot)

```json
{
  "pid": 536223,
  "name": "apt",
  "cmdline": ""
}
```

### systemd

- Unit `setuphelfer-backup@e0bba3dff5e5.service`: **failed** nach Abbruch
- **tar_stderr_log:** `/var/log/setuphelfer/backup-e0bba3dff5e5.log` (nur tar-Hinweise, keine Paketzeile)

---

## Phase 2 — Root Cause UPDATE-CONFLICT-041 (`e0bba3dff5e5`)

### Erkennungslogik zum Abbruchzeitpunkt

**Git HEAD** (`package_activity.py`, vor Workspace-Änderung) blockierte jeden Prozess mit Namen **`apt`**, unabhängig von der Kommandozeile:

```python
return name_l in {"apt", "apt-get", "dpkg", "apt.systemd.daily"}
```

**Laufzeit unter `/opt/setuphelfer/backend`** (Forensik-Snapshot 2026-05-16): verfeinerte Logik — nackter `apt` ohne mutierende Subkommandos → **nicht blockierend** (`is_blocking_package_activity('apt ', 'apt')` → `False`).

### Klassifikation

| Feld | Wert |
|------|------|
| **Primärklasse** | UPDATE-CONFLICT-041 |
| **Untertyp** | **False positive (Prozessname `apt`, leere cmdline)** unter alter Blockier-Regel *oder* kurzlebiger `apt`-Prozess ohne persistierte cmdline |
| **Mutierend?** | **Nicht nachweisbar** — kein `apt install` / `apt-get` in `active_package_processes` |
| **Timer-Kollision zum Abbruch (17:24 CEST)** | **Unwahrscheinlich** — relevante Units inaktiv seit Stunden |

### Timer / Services (Snapshot ~18:00 CEST)

| Unit / Timer | Zustand | Letzter Lauf (ca.) |
|--------------|---------|-------------------|
| `apt-daily.service` | inactive | Timer nicht fällig |
| `apt-daily-upgrade.service` | inactive | ~06:33 CEST |
| `mintupdate-automation-upgrade.service` | inactive | ~07:11 CEST |
| `packagekit.service` | inactive | — |
| `unattended-upgrades.service` | inactive | beendet ~14:16 CEST |

**Nächste relevante Timer (nach Abbruch):**

- `prometheus-node-exporter-apt.timer` → `prometheus-node-exporter-apt.service` (~17:49 CEST): **read-only** (`apt_info.py` → Prometheus-Metriken, kein dpkg-Lock)
- `prometheus-node-exporter-apt` **nach** Abbruch von `e0bba` — kein Kausalzusammenhang

### Prozesse / Locks zum Forensik-Zeitpunkt

- **Keine** laufenden `apt`/`dpkg`/`mintupdate`/`unattended` (außer Analyse-Shell)
- **`sudo lsof` auf dpkg-Locks:** nicht ausführbar (Passwort erforderlich) — dokumentiert, nicht interpretiert

### Journal

- `journalctl` ohne elevated Rechte: **keine auswertbaren Zeilen** im 4h-Fenster (Berechtigung)
- Empfehlung Host: `sudo journalctl --since "2026-05-16 17:20" --until "2026-05-16 17:25" | grep -Ei 'apt|dpkg|mint'`

### Vergleich 2026-05-13 (`e341a326ac69`)

Früherer BR-001-Abbruch mit **nachweislich mutierendem** `apt-get autoremove --purge -y` (Mint-Automation). Siehe `BR-001_package_activity_failure_2026-05-13.md`.

**`e0bba3dff5e5` unterscheidet sich:** nur `name=apt`, **leere cmdline** — passt zu **Namens-Blockade** der alten Regel, nicht zu dokumentiertem `apt-get autoremove`.

---

## Phase 1 — Job `927469d42503` (laufend, Snapshot)

| Feld | Wert |
|------|------|
| **status** | `running` |
| **phase** | `archiving` |
| **archive_path** | `/media/setuphelfer/br001/pi-backup-full-20260516_172457.tar.gz` |
| **partial** | ~45 GiB (Snapshot ~18:01 CEST) |
| **MainPID** | 537002 (`backup_runner.py` unter `/opt`) |
| **RAM (systemd)** | ~14.9G peak |
| **stderr** | `/var/log/setuphelfer/backup-927469d42503.log` |

**Kein Eingriff** in diesen Lauf.

---

## Phase 3 — Kernel / USB

`journalctl -k -n 200` (grep usb/ext4/I/O): **keine Treffer** → **NO_USB_ERRORS_IN_WINDOW** (im geprüften Fenster).

---

## Empfehlungen (keine Produktivänderung in diesem Task)

1. **Workspace-`package_activity.py` deployen** (feinere `apt`-Erkennung) — erst nach dokumentierter Freigabe / Gate, **nicht** während aktivem Lauf.
2. Vor Langläufern: **Preflight** `detect_active_package_operations()` + manuell `ps`/`systemctl list-timers` (Runbook `BR-001_package_activity_retry_runbook_2026-05-13.md`).
3. Optional Host: `sudo journalctl` um PID **536223** zum Abbruchzeitpunkt zu rekonstruieren.
4. **`prometheus-node-exporter-apt`:** als read-only einstufen; bei Bedarf Timer außerhalb Backup-Fenster planen.

---

## Verify Deep / BR-001-Abschluss

**Ausstehend** bis Job `927469d42503` mit finalem `.tar.gz` endet. Kein Verify, kein SHA256, kein grünes BR-001 ohne echten Erfolg.

Watcher (lokal, read-only): `/tmp/br001_watch_927469d42503.sh` → Log `/tmp/br001_watch_927469d42503.log`

---

*Erstellt: 2026-05-16, STRICT forensics-only.*
