# Backup performance: gzip vs pigz

## Auto mode (default)

- `SETUPHELFER_BACKUP_COMPRESSION_ENGINE=auto`
- If `pigz` is on PATH: `tar --use-compress-program=pigz …`
- Else: `tar -czf` (gzip), warning `compression_fallback_gzip`

No automatic package install — operator must provide pigz.

## Environment variables

See German doc `BACKUP_PERFORMANCE_DE.md` for the table.

## Explicit pigz missing

- `engine=pigz` without binary → preflight block `backup.compression_unavailable`.

## BR-001 / full-root-stable

- **pigz** speeds compression only; **tar** read phase stays single-threaded.
- **`full-root-stable`** excludes **Timeshift** (`/timeshift`) and volatile caches to avoid live-snapshot `tar_failed`.
- **`full-expert`** remains maximal and may fail on changing snapshot files.

## Runtime notes

- Full-root on live systems can take hours (gzip/pigz).
- Dashboard warns after 2h with gzip; stale progress after 5 minutes without byte growth.
