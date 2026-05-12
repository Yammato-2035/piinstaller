# Release Readiness – Bericht

**Generiert:** 2026-05-12 (STRICT — produktiver target-check, Deploy-Versuch, Rollback)  
**Gesamtstatus:** `blocked`

## Kurzfassung

**GitHub Actions `ci.yml`:** Run **25751304968** — **success** (HEAD `55d7cec`). **BR-001:** Produktiver **`GET /api/backup/target-check?backup_dir=/mnt/setuphelfer/backups`** → **`backup.path_invalid`** / **STORAGE-PROTECTION-004** (`nvme0n1p2[/mnt]`). Freigabe **nur /dev/sdd1** passt nicht zum Ist-Layout (**setuphelfer-back** auf **sda1**, **sdd1** = anderes Volume). Kurzzeitiger Dateikopie-Deploy nach `/opt/setuphelfer/backend` wurde **zurückgerollt** (`/tmp/setuphelfer-deploy-backup-20260512T194722Z`). **`systemctl restart`** und **`sudo -u setuphelfer`**-Tests: nicht ohne interaktives Passwort. Vollständige Spur: `BR-001_productive_target_check_2026-05-12.md`, `BR-001.json`.

## Ampelüberblick

| Bereich | Status |
|---------|--------|
| Backup/Restore/Verify (Evidence) | Rot (BR-001 **blocked** — produktiver target-check fehlgeschlagen) |
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
