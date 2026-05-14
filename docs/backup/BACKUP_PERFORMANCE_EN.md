# Backup performance architecture (Setuphelfer)

## Current state

- **Full-root** `tar` over `/` moves huge byte volumes; **gzip** is effectively **single-threaded**, so a 16C/32T machine often stays underutilised while wall time is dominated by I/O and compression.
- **Finalisation** (manifest embed) still assumes **gzip** tarstreams (`r:gz` / `w:gz`). **zstd** is **detected and documented** in `compression_detail`, but **not** used for the final archive until the finalize path is extended.

## Target design

1. **Compression (gzip-compatible):** prefer **pigz** when installed; else **`tar -czf`**.  
2. **zstd:** planned with explicit archive suffix and finalize support; candidate flags documented (`zstd -T0 -3` desktop, `-1` Pi-like).  
3. **Profiles:** `recommended` (default), `fast-system`, `user-data`, `developer`, `full-expert` (explicit only, emits warning code).  
4. **Excludes:** keep mandatory safety excludes; `recommended` adds optional `/var/cache`, `/var/tmp`.  
5. **Progress:** structured `progress_optional` — see `core/backup_progress.py`; **ETA** only when `bytes_total_estimate` is reliable, else `null`.

## Matrix IDs

- **BR-016** performance & compression  
- **BR-018** progress / ETA  
- **BR-019** profiles  

(Legacy **BR-012** finalization fix; **BR-013** target write I/O.)

## UI progress & evidence (2026-05-14)

- **`RunningBackupModal`** and **Create backup** (`BackupRestore`) render structured **`progress_optional`**: phase, operation, compression, human-readable bytes, throughput, elapsed time, **ETA only with reliable `bytes_total_estimate`** (else `backup.messages.eta_unknown`), target free space, `warning_codes`, `health_flags`.
- **No archive percent bar** without a positive **`bytes_total_estimate`** (copy explains active progress without percent).
- **Evidence bundle:** buttons call **`GET`/`POST /api/backup/jobs/{job_id}/evidence`** (see `BACKUP_EVIDENCE_COLLECTOR_*.md`).
- Frontend unit tests: `npm run test` → `src/utils/backupJobProgressDisplay.test.ts` (Vitest).
