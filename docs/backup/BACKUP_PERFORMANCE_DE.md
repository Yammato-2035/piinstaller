# Backup-Performance und Architektur (Setuphelfer)

## Ist-Zustand

- **Full-Root** (`tar` über `/`) erzeugt riesige Datenmengen; **gzip** komprimiert **single-threaded** → auf 16C/32T bleibt CPU meist unten genutzt, Laufzeit wächst mit Datenmenge und Ziel-I/O.
- **Finalisierung** (`MANIFEST`-Einbettung) arbeitet weiterhin auf **gzip**-Streams (`tarfile` `r:gz`/`w:gz`); ein Wechsel auf **zstd** erfordert angepasste Finalize-Pipeline und klare Archiv-Endungen — im Repo **vorbereitet** (`zstd_available`, Metadaten), **noch nicht** produktiv für das fertige Archiv.

## Zielbild

1. **Kompression (gzip-kompatibel):** bevorzugt **pigz** (parallel gzip), Fallback **`tar -czf`** — kein Bruch der bestehenden Finalisierung.
2. **zstd:** später `--use-compress-program` + Finalize-Anpassung; Default-Kandidaten dokumentiert (`zstd -T0 -3` Desktop, `-1` Pi-ähnlich).
3. **Profile:** `recommended` (Default), `fast-system`, `user-data`, `developer`, `full-expert` — letzterer **nur explizit**, mit Warn-Code in `profile_warnings`.
4. **Excludes:** Safety-Excludes unverändert; Profil **`recommended`** ergänzt optional `/var/cache`, `/var/tmp` (keine pauschale Entfernung von Nutzerdaten).
5. **Fortschritt:** `progress_optional` mit `phase`, Durchsatz, `eta_seconds` nur wenn belastbar, sonst `null` — siehe `core/backup_progress.py`.

## Matrix

- **BR-016** Performance & Kompression  
- **BR-018** Progress / ETA  
- **BR-019** Profile  

(Historisch **BR-012** = Finalisierungs-Fix; **BR-013** = Schreib-EIO.)

## UI-Fortschritt und Evidence (2026-05-14)

- **`RunningBackupModal`** und **Backup erstellen** (`BackupRestore`) zeigen strukturiertes **`progress_optional`**: Phase, Aktion, Kompression, Datenmenge (human-readable), Durchsatz, Laufzeit, **Restzeit nur bei belastbarer Gesamtgröße** (sonst i18n `backup.messages.eta_unknown`), Ziel frei, Warnungen (`warning_codes`), Health-Flags.
- **Keine Prozentanzeige** ohne positives **`bytes_total_estimate`** (Hilfstext „Fortschritt aktiv …“).
- **Diagnosepaket:** Buttons rufen **`GET`/`POST /api/backup/jobs/{job_id}/evidence`** auf (siehe `BACKUP_EVIDENCE_COLLECTOR_*.md`).
- Frontend-Unit-Tests: `npm run test` → `src/utils/backupJobProgressDisplay.test.ts` (Vitest).
