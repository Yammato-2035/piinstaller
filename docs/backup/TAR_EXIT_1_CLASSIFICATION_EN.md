# GNU tar exit code 1 – classification (Setuphelfer)

**As of:** 2026-05-17 · **Evidence:** `docs/evidence/runtime-results/br001_tar_exit1_forensics_2026-05-16.json` (job `927469d42503`)

## Background

GNU **tar** exits with code **1** when **warnings** occurred during the run (e.g. live file changes, ignored sockets), even if the stream was written to the end. That does **not** automatically mean the archive is useless — and it does **not** mean Setuphelfer may mark the job as success.

The isolated runner (`backend/tools/backup_runner.py`) currently treats **any** pipeline `returncode != 0` as **`abort_reason: tar_failed`**, deletes the `.partial` file, and produces **no** final `.tar.gz` (no SHA256, no verify deep).

## Classification levels (design)

| ID | Meaning |
|----|---------|
| `TAR_OK` | Exit 0, no fatal messages |
| `TAR_LIVE_FILE_CHANGED_ONLY` | Exit 1, only “file changed” on **volatile** paths |
| `TAR_SOCKET_IGNORED_ONLY` | Exit 1, only “socket ignored” on **volatile** paths |
| `TAR_VOLATILE_WARNINGS_ONLY` | Exit 1, mix of allowed volatile warnings |
| `TAR_CRITICAL_WARNING` | e.g. file change under `/etc`, `/boot` |
| `TAR_IO_ERROR` | I/O error, short write on target stream |
| `TAR_PERMISSION_CRITICAL` | Permission denied on critical path |
| `TAR_FATAL` | Unexpected messages, EOF, disk full, other exit 1 |

Implementation: `backend/core/backup_tar_warning_classification.py` — integrated in the isolated runner (`backend/tools/backup_runner.py`) as of 2026-05-17 (workspace; deploy separately).

## Hard rules (safety)

Exit **1** may only be downgraded from hard failure when **all** apply:

1. No I/O errors, no “no space left”, no “unexpected EOF”
2. No critical system paths in warnings (`/etc`, `/boot`, `/usr`, …)
3. Only allowed volatile patterns (see knowledge base)
4. **Final** `.tar.gz` exists
5. **SHA256** of archive payload OK
6. **Verify deep** OK

Without a final archive: status stays **`failed`** / **`blocked`**, never **`success`**.

## BR-001 run 927469d42503 (summary)

- Profile **`full-expert`**, ~**227 GiB** in `.partial`, then exit **1**
- Stderr: gpg-agent sockets, Docker Desktop sockets, many ibus cache sockets, **one** journal file change
- **No** I/O / disk full / EOF / critical permission messages
- Warning classification: **`TAR_VOLATILE_WARNINGS_ONLY`**
- Operational outcome: **`failed`** (partial removed, no archive)

## Stable tar profile (proposal)

### Additional excludes (full-expert / BR-001)

Already on `recommended` / `fast-system`: `/var/cache`, `/var/tmp`.

Consider for volatile live data:

| Pattern | Rationale |
|---------|-----------|
| `/var/log/journal` | journal grows/rotates during backup |
| `/home/*/.cache` | browser, ibus, desktop caches |
| `/home/*/.local/share/Trash` | trash |
| Browser profile caches | e.g. under `.var/app/.../cache` |

**Docker Desktop** (`~/.docker/desktop/*.sock`, VM sockets): do **not** blanket-exclude from root backup without a strategy — options: separate Docker backup, stop services/snapshot, or treat as **non-deterministic** live data and rely on verify deep.

### Option `--warning=no-file-changed`

| Aspect | Assessment |
|--------|------------|
| Benefit | Fewer exit-1 from journal/logs; more stable exit code |
| Risk | Hides real changes on **non-volatile** paths |
| Exit code | Stabilizes **file-changed** warnings only, not sockets or I/O |
| Verify deep | **Still mandatory** — quieter stderr ≠ integrity |

### Not used: `--ignore-failed-read`

Silently skips unreadable files and weakens safety gates. Setuphelfer rejects this option.

## Runner integration (workspace)

After the `tar` pipeline (`subprocess_returncode != 0`):

1. Classify full stderr; persist fields on `status.json` (see DE doc for field list).
2. **Volatile-only** + readable `.partial` → finalize (SHA256, manifest, rename) and **verify deep** in the runner.
3. Success only as `backup.success_with_warnings` with `warning_status: completed_with_warnings` and `backup_integrity_status: verified`.
4. **No** final archive → `backup.warning_not_promoted`, partial cleanup unchanged.
5. I/O, disk full, EOF, critical paths → hard `backup.failed`.

**No blanket success on exit 1.** BR-001 stays red without the integrity chain.

## Next steps (no automatic BR-001)

1. Deploy runner to `/opt` after explicit approval; re-run runtime gate.
2. Prefer `recommended` over `full-expert` for routine backups.
3. Keep Docker/journal evidence documented.

## References

- FAQ: `docs/faq/BACKUP_RESTORE_FAQ_EN.md` (tar exit 1 section)
- KB: `docs/knowledge-base/backup/TAR_EXIT_1_LIVE_FILES.md`
- Tests: `backend/tests/test_backup_tar_warning_classification_v1.py`
