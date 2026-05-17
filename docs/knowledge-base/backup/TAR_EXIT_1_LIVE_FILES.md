# Knowledge Base: tar exit 1 and live/volatile files

**Related:** `docs/backup/TAR_EXIT_1_CLASSIFICATION_DE.md`, diagnosis forensics job `927469d42503`

## Why tar exit 1 does not always mean a broken backup

GNU tar uses exit code **1** for “completed with warnings”. Typical warnings on live systems:

- **File changed as we read it** — file content changed while tar read it (logs, databases, journals).
- **Socket ignored** — tar does not archive socket nodes; this is expected for agent sockets.

A large partial archive may still be structurally complete, but Setuphelfer **does not** assume that from exit code alone.

## Why Setuphelfer does not blindly accept exit 1

Current runner behavior (`backup_runner.py`, `rc != 0` branch):

- Sets `abort_reason: tar_failed`
- Deletes `.partial` when configured
- Skips SHA256, manifest finalize, rename, verify deep

Rationale: without classification and post-checks, exit 1 is indistinguishable from real failure (I/O, truncated stream, critical path issues).

Classifier: `backend/core/backup_tar_warning_classification.py`. Wired in `backend/tools/backup_runner.py` (workspace). Production requires deploy to `/opt` and a green runtime gate.

Volatile-only is **not** automatic success: the runner may attempt finalize + verify deep on a complete `.partial`, but promotes to `backup.success_with_warnings` only after SHA256 and verify deep succeed.

## Volatile path policy

Paths treated as **volatile** for warning downgrade (not for skipping without operator policy):

| Category | Examples |
|----------|----------|
| Temp/cache | `/var/tmp`, `/var/cache` (excluded on recommended profile) |
| Journal | `/var/log/journal/...` |
| User cache | `/home/*/.cache/**` (ibus, browser caches) |
| Agent sockets | `/root/.gnupg/S.*`, `~/.docker/desktop/*.sock` |
| Trash | `/home/*/.local/share/Trash` |

**Critical** paths (never downgrade on “file changed”): `/etc`, `/boot`, `/usr`, `/var/lib/dpkg`, `/var/lib/apt`.

## Docker

Docker Desktop on a desktop host exposes Unix sockets and VM state under `~/.docker/desktop/`. Options:

1. **Separate backup** of Docker volumes/data directory with containers stopped.
2. **Stop Docker** / snapshot before full-root BR-001.
3. **Document as non-deterministic** — if included in full-expert root tar, require verify deep and accept possible exit 1 from sockets unless excluded.

Do **not** add a blanket `--exclude=/var/lib/docker` without documenting restore impact.

## SHA256 and verify deep after warnings

Even if warnings are classified as volatile-only:

1. Final `.tar.gz` must exist.
2. Payload SHA256 must match embedded manifest hash.
3. **Verify deep** must pass (member policy, checksums, manifest).

Only then may an operator-facing status consider “success with warnings” — never from stderr alone.

## No success without final archive

Job `927469d42503`: ~227 GiB written, `subprocess_returncode: 1`, `partial_deleted: true`, no `pi-backup-full-*.tar.gz`.

Therefore:

- `sha256_skipped_reason`: no final archive
- `verify_deep_skipped_reason`: no final archive
- API/runner status: **`backup.failed`**

## `--warning=no-file-changed` (evaluation)

- Suppresses **file-changed** warnings only; sockets and I/O still affect exit code.
- Risk: silent loss of signal on important paths if excludes are wrong.
- Does **not** replace verify deep.

## Rejected: `--ignore-failed-read`

Would skip unreadable files without failing the job — incompatible with Setuphelfer safety gates and manifest completeness goals.
