# Backup Evidence Collector

## Zweck

Nach Abschluss eines Backup-Jobs (Erfolg oder Fehler) werden Diagnosedaten gesammelt, ohne den Job zu verändern.

## Ausgabe

1. `/var/lib/setuphelfer/evidence/backup-jobs/<job_id>/`  
2. Falls nicht beschreibbar: `/tmp/setuphelfer-evidence-<job_id>/`

## Inhalt (Manifest + Dateien)

- Kopie von `status.json`, `job.json`, `backup-<job_id>.log` (falls vorhanden)
- Ausgaben von `systemctl status/show`, `journalctl` (Unit + Kernel), `dmesg` (falls erlaubt)
- SHA256 von `/opt/setuphelfer/backend/tools/backup_runner.py` und `app.py` (nur Digest, keine vollen Dateien)
- Bei fehlenden Rechten: Einträge `permission_denied` im `manifest.json`, trotzdem nutzbares Paket

## Aufruf

- Automatisch am Ende des Runners (`_mark_terminal`), sofern Pipeline-Kontext gesetzt ist.
- Manuell: `python3 backend/tools/backup_evidence_collector.py --job-id <ID> [--status-dir …] [--backup-dir …]`
