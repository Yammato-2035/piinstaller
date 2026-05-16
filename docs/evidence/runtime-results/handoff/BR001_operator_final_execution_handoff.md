# BR-001 — Finaler Operator-Handoff (Full Root, externes Ziel, STRICT)

**Status:** Kein Backup in diesem Dokument gestartet. Kein simuliertes Verify. Kein internes Ziel (`/` oder nur `/mnt/setuphelfer/backups` auf Root-FS ist **kein** BR-001-externes Ziel).

**Voraussetzungen:** Runtime-Gate grün (`./scripts/check-runtime-deploy-gate.sh` Exit 0), `ReadWritePaths` der Units enthalten `/media/setuphelfer` (siehe Repo-Units + Drop-in-Beispiele).

---

## Phase 0 — Runtime Gate (vor jedem Lauf)

```bash
cd /opt/setuphelfer
# oder Workspace:
# cd /pfad/zum/piinstaller

./scripts/check-runtime-deploy-gate.sh
```

```bash
curl -s http://127.0.0.1:8000/api/dev-dashboard/status \
  | jq '.dashboard.runtime_gate.passed, .dashboard.deploy_drift.status, .dashboard.safe_test_mode.mode'
```

Erwartung: `true`, `"green"`, `"UNLOCKED"`. Sonst **STOP**.

---

## Phase 1 — Externes Medium und Zielpfad

**Konstante für alle folgenden Befehle** (anpassen, aber nicht unter `/media/<login>`):

```bash
export BR001_LABEL=br001
export BR001_DIR="/media/setuphelfer/${BR001_LABEL}"
```

### 1.1 Medium und Mount prüfen

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,UUID,MOUNTPOINTS,MODEL,TRAN,RM
```

```bash
findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS,AVAIL,USED
```

```bash
sudo blkid
```

Sicherstellen: Zielpartition ist **ext4** (oder anderes von der Produktsicherheit zugelassenes FS) auf **USB/removable**, nicht Root-`nvme`… als „extern“ getarnt.

### 1.2 Zielstruktur anlegen (einmalig, mit sudo)

**Hinweis:** `/media/setuphelfer` muss auf dem **gemounteten externen Dateisystem** liegen oder Sie mounten die Partition explizit nach `/media/setuphelfer` (fstab). Unten: Verzeichnis auf dem bereits gemounteten externen Tree.

```bash
sudo install -d -o root -g setuphelfer -m 0770 "${BR001_DIR}"
```

(Äquivalent zu `mkdir` + `chown` + `chmod`; **kein** `chmod 777`.)

### 1.3 Schreibtest als Dienstnutzer

```bash
sudo -u setuphelfer touch "${BR001_DIR}/.write_probe" && sudo -u setuphelfer rm -f "${BR001_DIR}/.write_probe"
```

Fehlschlag → Gruppe/Rechte oder systemd `ReadWritePaths` prüfen, Backend neu starten.

### 1.4 Backend nach Unit-Änderung

```bash
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
systemctl is-active setuphelfer-backend.service
```

### 1.5 API target-check

```bash
curl -sG 'http://127.0.0.1:8000/api/backup/target-check' \
  --data-urlencode "backup_dir=${BR001_DIR}"
```

Optional mit Anlegen leerer Hierarchie (nur wenn Pfad noch fehlt — vorher 1.2 ausführen bevorzugt):

```bash
curl -sG 'http://127.0.0.1:8000/api/backup/target-check' \
  --data-urlencode "backup_dir=${BR001_DIR}" \
  --data-urlencode 'create=0'
```

Erwartung: Antwort mit `"status":"success"` (Contract-Felder je nach Client). Fehler typisch:

| Hinweis | Bedeutung |
|-----------|-----------|
| `STORAGE-PROTECTION-001` | Ziel wirkt wie System-/unsicherer Mount — Mount/UUID prüfen. |
| `BACKUP-TARGET-USER-MOUNT-003` | Pfad unter `/media/<anderer_login>/` — nicht verwenden. |
| `BACKUP-TARGET-PERMISSION-001` / `002` | Rechte oder systemd-Sandbox. |
| `UPDATE-CONFLICT-041` | später beim **create**, nicht target-check: Paketmanager aktiv. |

---

## Phase 2 — Package Freeze (temporär, kein disable/mask)

### Stoppen

```bash
sudo systemctl stop mintupdate-automation-upgrade.timer
sudo systemctl stop apt-daily.timer
sudo systemctl stop apt-daily-upgrade.timer
```

### Status nach Stop

```bash
systemctl is-active mintupdate-automation-upgrade.timer apt-daily.timer apt-daily-upgrade.timer
```

Erwartung je Zeile: `inactive`.

### Blocker prüfen (keine apt/dpkg)

```bash
pgrep -a apt || true
pgrep -a dpkg || true
pgrep -a unattended-upgrade || true
```

### Nach Backup wieder an

```bash
sudo systemctl start mintupdate-automation-upgrade.timer
sudo systemctl start apt-daily.timer
sudo systemctl start apt-daily-upgrade.timer
```

```bash
systemctl is-active mintupdate-automation-upgrade.timer apt-daily.timer apt-daily-upgrade.timer
```

Erwartung: `active` (oder `inactive` bei mintupdate, je nach Distribution — dokumentieren, was bei Ihnen „normal“ ist).

---

## Phase 3 — Full Root starten (API)

**JSON-Body** (Felder wie im Backend: `type`, `backup_dir`, `confirm_full_expert`, `async`, `target`; bei Bedarf `sudo_password` nur wenn Ihre Installation das verlangt — nicht in Logs committen):

```bash
curl -s -X POST 'http://127.0.0.1:8000/api/backup/create' \
  -H 'Content-Type: application/json' \
  -d "$(jq -n \
    --arg dir "${BR001_DIR}" \
    '{type:"full",backup_dir:$dir,confirm_full_expert:true,async:true,target:"local"}')"
```

Erwartung bei Erfolg: `"status":"accepted"`, `"job_id":"…"`, `message_key`/Contract z. B. `backup.job_started`. Fehler typisch:

| Code / Key | Situation |
|------------|-----------|
| `backup.full_expert_confirmation_required` | `confirm_full_expert` fehlt oder `false`. |
| `backup.blocked_package_activity` | `UPDATE-CONFLICT-041` — apt/dpkg läuft. |
| `backup.path_invalid` | Ziel ungültig; `details.diagnosis_id` kann `BACKUP-TARGET-*` oder `STORAGE-*` sein. |
| `backup.job_conflict` | anderer Job aktiv. |
| `backup.runner_start_failed` | systemd-Runner; `SYSTEMD-RUNNER-001`. |

```bash
RESP="$(curl -s -X POST 'http://127.0.0.1:8000/api/backup/create' \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg dir "${BR001_DIR}" '{type:"full",backup_dir:$dir,confirm_full_expert:true,async:true,target:"local"}')")"
echo "$RESP" | jq .
JOB_ID="$(echo "$RESP" | jq -r '.job_id // empty')"
echo "JOB_ID=${JOB_ID}"
```

Falls `JOB_ID` leer: Response zeigt `status":"error"` und `details` / `code` (z. B. Pfad, Package-Blocker).

### Polling Job

```bash
curl -s "http://127.0.0.1:8000/api/backup/jobs/${JOB_ID}" | jq '{status: .job.status, code: .job.code, severity: .job.severity, backup_file: .job.backup_file}'
```

Terminal-Schleife (Beispiel, alle 60 s):

```bash
while true; do
  curl -s "http://127.0.0.1:8000/api/backup/jobs/${JOB_ID}" \
    | jq -c '{t: now|todate, status: .job.status, code: .job.code}'
  ST=$(curl -s "http://127.0.0.1:8000/api/backup/jobs/${JOB_ID}" | jq -r .job.status)
  case "$ST" in success|error|cancelled) break ;; esac
  sleep 60
done
```

**systemd:**

```bash
systemctl status "setuphelfer-backup@${JOB_ID}.service" --no-pager
journalctl -u "setuphelfer-backup@${JOB_ID}.service" -e --no-pager
```

### SHA256 (Betreiber, nach fertigem Archiv)

Archivpfad aus letztem erfolgreichen Job oder `ls -lt "${BR001_DIR}"/pi-backup-full-*.tar.gz | head -1`:

```bash
ARCHIVE="${BR001_DIR}/pi-backup-full-XXXXXXXX_XXXXXX.tar.gz"
test -f "$ARCHIVE"
sha256sum "$ARCHIVE" | tee "${ARCHIVE}.sha256"
```

---

## Phase 4 — Verify Deep (nur wenn `.tar.gz` vollständig, keine `.partial`)

```bash
curl -s -X POST 'http://127.0.0.1:8000/api/backup/verify' \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg f "$ARCHIVE" '{backup_file:$f,mode:"deep"}')"
```

Erwartung: `data.results.valid == true` bzw. Contract-`status` success. Fehler: `backup.verify_partial_not_allowed`, `backup.verify_archive_unreadable`, Integritäts-Codes in den Details — **kein** manuelles „grün“ ohne Response-Body.

---

## Phase 5 — Monitoring (parallel in echten Terminals)

```bash
journalctl -kf
```

```bash
lsusb -t
```

```bash
iostat -xz 5
```

oder falls installiert:

```bash
vmstat 5
```

**Cockpit (Frontend):**

```bash
cd /pfad/zum/piinstaller/frontend
npm run tauri:dev-cockpit
```

---

## Governance / Evidence nach Erfolg

- Evidence-JSON/MD mit: Job-ID, Start/Ende, Archivgröße, `sha256sum`, Verify-Laufzeit, Package-Freeze-Zeiten.
- `CORE_RECOVERY_TEST_RETURN.md`: BR-001 Full Root nur auf **„validated“** setzen, wenn **reales** Archiv + **verify deep** success vorliegen.
- Restore/Rescue bleiben rot, bis eigene Phasen abgeschlossen sind — **kein** Fake-Grün.

---

## Referenzen (Repo)

- `docs/knowledge-base/storage/external-backup-target-architecture.md`
- `docs/knowledge-base/runtime/systemd-backup-service-backup-targets.md`
- `docs/operations/systemd/setuphelfer-backend-backup-target.conf.example`
- `packaging/systemd/setuphelfer-backup@.service`
