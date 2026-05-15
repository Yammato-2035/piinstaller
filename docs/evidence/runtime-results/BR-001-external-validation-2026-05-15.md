# BR-001 — Externe Backup-Validierung (2026-05-15)

## Ergebnis

**Teilvalidiert (gelb):** Echtes externes **Daten**-Backup auf `/media/gabriel/setuphelfer-back1` (`/dev/sda1`, ext4), gefolgt von erfolgreichem **Verify** (deep). Kein Restore, kein Full-Root-Backup.

## Phase 0

- `./scripts/check-runtime-deploy-gate.sh` → Exit 0
- `runtime_gate.passed=true`, `deploy_drift=green`, `safe_test_mode=UNLOCKED`

## Zielmedium

| Feld | Wert |
|------|------|
| Gerät | `/dev/sda1` |
| Mount | `/media/gabriel/setuphelfer-back1` |
| UUID | `adbd53e5-26fd-4723-b0f1-1880dbaa2719` |
| FS | ext4 |
| Frei | ~679 GiB |

`/media/gabriel/setuphelfer-back` ist **kein** externes Mount (leer auf Root-NVMe) — Write-Guard blockiert korrekt.

## Backup (echt)

- **Job:** `9481e637d8db`
- **Archiv:** `pi-backup-data-20260515_192328.tar.gz` (570 B)
- **SHA256:** `489efb1e4966135485cec126fc0f591b44c740d8bf268dd1490161474035c5ff`
- **Quelle:** `/mnt/setuphelfer/test-data` (Service-Env `SETUPHELFER_DATA_BACKUP_SOURCES`)
- **Profil:** `recommended` → `data`
- `.partial` atomisch entfernt; `MANIFEST.json` im Archiv

## Verify (echt)

- `POST /api/backup/verify` → `backup.verify_success`, `valid: true`, mode `deep`

## Runtime-Fixes (ohne Gate-Schwächung)

1. Starter mit `setuphelfer-back1` in `ALLOWED_BACKUP_ROOTS` + `SETUPHELFER_BACKUP_HELPER_PATH` unter `/opt`
2. systemd-Drop-in: `ReadWritePaths` + `PYTHONPATH` für Backup-Unit
3. `backup_runner.py`: `sys.path`-Bootstrap (systemd-Exec ohne uvicorn-CWD)

## Offen (ehrlich rot/gelb)

- **Full-Backup** (`type=full`, `/`) — nächster BR-001-Schritt
- Restore-Preview, Rescue, HW-E2E
- Release-Gate `backup_restore` bleibt rot bis Full-Kette + BR-002+

Maschinell: `BR-001-external-validation-2026-05-15.json`
