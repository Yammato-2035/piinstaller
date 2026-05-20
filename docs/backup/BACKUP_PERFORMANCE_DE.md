# Backup-Performance: gzip vs pigz

## Automatik (Standard)

- `SETUPHELFER_BACKUP_COMPRESSION_ENGINE=auto` (Default)
- Wenn `pigz` im PATH: `tar --use-compress-program='pigz -p N -L'`
- Sonst: `tar -czf` (gzip), Status `compression_fallback_gzip`

Kein automatisches `apt install` — pigz muss vom Betreiber bereitgestellt werden.

## Optionale Umgebungsvariablen

| Variable | Werte | Default |
|----------|--------|---------|
| `SETUPHELFER_BACKUP_COMPRESSION_ENGINE` | auto, gzip, pigz | auto |
| `SETUPHELFER_BACKUP_PIGZ_LEVEL` | 1–9 | 6 (Desktop), 2 (Pi-like) |
| `SETUPHELFER_BACKUP_PIGZ_THREADS` | auto oder Zahl | CPU-Kerne |

## Explizit pigz ohne Binary

- `engine=pigz` und pigz fehlt → Preflight-Block `backup.compression_unavailable` (kein stiller Fallback).

## Laufzeit-Hinweise

- Full-Root auf Live-Systemen kann viele Stunden dauern (gzip).
- Development Dashboard warnt ab 2 h Laufzeit mit gzip.
- Kein Fortschritt > 5 min → Stale-Warnung im Dashboard.
