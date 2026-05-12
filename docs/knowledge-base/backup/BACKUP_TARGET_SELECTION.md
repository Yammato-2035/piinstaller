# Backup-Zielauswahl — Wissensdatenbank

## Ziel

Eindeutig **externes**, **beschreibbares**, **nicht systemkritisches** Medium wählen; vorhandene Daten **nicht** löschen oder überschreiben; nur **freien Speicher** nutzen.

## Prioritätsliste (extern vor intern)

1. Externe NVMe (USB-NVMe)
2. Externe SSD (USB)
3. Externe HDD
4. USB-Stick
5. SD-Karte

Interne `nvme*n*` mit Mount `/` oder `/boot*` sind **keine** Kandidaten.

## Strategischer Pfad `/media/setuphelfer/setuphelfer-back`

- Nur sinnvoll, wenn dieser Baum **auf dem externen Kandidaten** liegt (Mount-Quelle ≠ Root-FS).
- Wenn der Betreiber weiterhin z. B. **`/media/<user>/setuphelfer-back`** nutzt: **keine** automatische Umdeutigung durch Setuphelfer — Freigabe/Mount-Konzept klären.
- Ohne Freigabe: **keine** `mkdir`/`chmod`/`chown`-Automatik.

## Prüfungen (lesend)

- `lsblk` (TRAN, RM, ROTA, FSTYPE, LABEL, UUID, MOUNTPOINTS)
- `findmnt` für `/media` und `/run/media`
- `df -hT` für freien Platz

## API

- `GET /api/backup/target-check?backup_dir=...&create=0` — **kein** Backup-Start.
- Nach Backend-Stand mit Traverse-Diagnose: bei gesperrtem Zwischenverzeichnis unter `/media` **`backup.target_traverse_denied`** / **STORAGE-PROTECTION-006** statt irreführender „Systemplatte“.

## Verweise

- `docs/backup/BACKUP_TARGET_POLICY_DE.md` / `BACKUP_TARGET_POLICY_EN.md`
- `docs/evidence/backup-restore/BR-001_external_target_policy_2026-05-12.md`
- `docs/evidence/backup-restore/BR-001_external_target_selection_2026-05-12.md`
