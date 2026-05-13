# BR-001 — Starter-Update und erneuter Backup-Versuch (STRICT, 2026-05-13)

**Ziel:** Produktiven **`/usr/lib/setuphelfer/setuphelfer-backup-starter`** aus dem Repository installieren und **BR-001 Full Backup** erneut nur auf **`/media/gabriel/setuphelfer-back`** starten. **Kein** Restore, **kein** anderer Zielpfad.

## Phase 0 — Backend-Version-Gate

| Prüfung | Ergebnis |
|---------|----------|
| `./scripts/check-backend-version-gate.sh` | **Exit 0** |
| `GET /api/version` | **HTTP 200**, `project_version` **1.7.1** |
| `setuphelfer-backend.service` | **active (running)** |

## Phase 1 — Starter-Stand

| Artefakt | Wert |
|----------|------|
| Repo-Datei | `packaging/helpers/setuphelfer-backup-starter.py` |
| **`ALLOWED_BACKUP_ROOTS`** im Repo | enthält **`/mnt/setuphelfer/backups`** und **`/media/gabriel/setuphelfer-back`** (Zeilen 17–20) |
| Produktiver Pfad | `/usr/lib/setuphelfer/setuphelfer-backup-starter` |
| **`grep ALLOWED_BACKUP_ROOTS` auf Produktion** | **kein Treffer** — installierte Version **vor** Repo-Anpassung (nur Legacy-Allowlist) |
| **SHA256 Workspace (Repo)** | `55615b84f867f35fdae09113716845207f322cbca2730e8e15ca41790fa1e771` |
| **SHA256 vor Install (Produktion, Stand 2026-05-13)** | `96341f48e5764cee895d48b6c06ba0a4aa84d29cd74ada42332c83bc1022325a` |
| **SHA256 nach Install** | **nicht erfasst** — Install nicht durchgeführt |

## Phase 2–3 — Backup + `sudo install` (STOP)

Geplantes Backup-Verzeichnis: **`/tmp/setuphelfer-starter-backup-20260513T162835Z`** (nur Konzept — **`sudo mkdir`** schlug fehl).

**Fehler:** `sudo: ein Terminal ist erforderlich … / Ein Passwort ist notwendig`

**Folge:** Kein Kopieren des alten Starters nach `/tmp/…`, kein **`sudo install`** des Repo-Starters → **produktiver Starter unverändert**.

## Phase 4 — Ziel vor Backup (nur lesend, trotzdem ausgeführt)

| Prüfung | Ergebnis |
|---------|----------|
| `findmnt -T /media/gabriel/setuphelfer-back` | **ext4**, **rw**, **SOURCE** `/dev/sdb1` |
| `lsblk` | **UUID** `adbd53e5-26fd-4723-b0f1-1880dbaa2719`, **LABEL** `setuphelfer-back`, USB, **nicht** Root-FS |
| `ReadWritePaths` | enthält **`/media/gabriel/setuphelfer-back`** |
| `target-check` | **`backup.target_check_ok`**, `mount_readonly`: **false** |

## Phase 5–9 — Backup / Job / Verify

**Nicht ausgeführt** — laut Vorgabe kein **`POST /api/backup/create`**, solange Phase 2–3 nicht erfolgreich (Starter nicht produktiv aktualisiert). **BR-004 / BR-005:** nicht ausgeführt.

## Operator-Runbook (nach Freigabe)

```bash
TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/tmp/setuphelfer-starter-backup-$TS"
sudo mkdir -p "$BACKUP"
sudo cp /usr/lib/setuphelfer/setuphelfer-backup-starter "$BACKUP/setuphelfer-backup-starter.before"
sha256sum /usr/lib/setuphelfer/setuphelfer-backup-starter | sudo tee "$BACKUP/SHA256SUMS.before"
sha256sum packaging/helpers/setuphelfer-backup-starter.py | sudo tee "$BACKUP/SHA256SUMS.workspace"
cd /home/volker/piinstaller
sudo install -o root -g root -m 0755 \
  packaging/helpers/setuphelfer-backup-starter.py \
  /usr/lib/setuphelfer/setuphelfer-backup-starter
sha256sum /usr/lib/setuphelfer/setuphelfer-backup-starter | sudo tee "$BACKUP/SHA256SUMS.after"
grep -n "ALLOWED_BACKUP_ROOTS" -A15 /usr/lib/setuphelfer/setuphelfer-backup-starter
```

Anschließend **`target-check`** erneut, dann **`POST /api/backup/create`** mit dem exakt freigegebenen JSON (siehe `BR-001_full_backup_run_2026-05-13.md`).

## Ergebnis

| Punkt | Status |
|-------|--------|
| Starter produktiv aktualisiert | **Nein** (sudo blockiert im Agent) |
| BR-001 erneut gestartet | **Nein** |
| BR-004 / BR-005 | **blocked** |
| Restore | **Nein** |
