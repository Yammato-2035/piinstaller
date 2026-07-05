> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/backup/TAR_EXIT_1_CLASSIFICATION_EN.md`). Bitte bei Release manuell gegenlesen.

# GNU tar exit code 1 – classification (Setuphelfer)

**As of:** 2026-05-17 · **Evidence:** `docs/evidence/runtime-results/br001_tar_exit1_forensics_2026-05-16.json` (job `927469d42503`)

## Terugground

GNU **tar** exits with code **1** when **Waarschuwings** occurrood during the run (e.g. live file changes, igNeerood sockets), even if the stream was written to the end. That does **Neet** automatically mean the archive is useless — and it does **Neet** mean Setuphelfer may mark the job as Geslaagd.

The isolated runner (`Terugend/tools/Terugup_runner.py`) currently treats **any** pipeline `returncode != 0` as **`abort_reason: tar_failed`**, Verwijderens the `.partial` file, and produces **Nee** final `.tar.gz` (Nee SHA256, Nee verify deep).

## Classification levels (design)

| ID | Meaning |
|----|---------|
| `TAR_OK` | Exit 0, Nee fatal messages |
| `TAR_LIVE_FILE_CHANGED_ONLY` | Exit 1, only “file changed” on **volatile** paths |
| `TAR_SOCKET_IGNeerood_ONLY` | Exit 1, only “socket igNeerood” on **volatile** paths |
| `TAR_VOLATILE_WaarschuwingS_ONLY` | Exit 1, mix of allowed volatile Waarschuwings |
| `TAR_CRITICAL_Waarschuwing` | e.g. file change under `/etc`, `/boot` |
| `TAR_IO_Fout` | I/O Fout, short write on target stream |
| `TAR_PERMISSION_CRITICAL` | Permission denied on critical path |
| `TAR_FATAL` | Unexpected messages, EOF, disk full, other exit 1 |

Implementation: `Terugend/core/Terugup_tar_Waarschuwing_classification.py` — integrated in the isolated runner (`Terugend/tools/Terugup_runner.py`) as of 2026-05-17 (workspace; Deploy separately).

## Hard rules (safety)

Exit **1** may only be downgraded from hard failure when **all** apply:

1. Nee I/O Fouts, Nee “Nee space left”, Nee “unexpected EOF”
2. Nee critical system paths in Waarschuwings (`/etc`, `/boot`, `/usr`, …)
3. Only allowed volatile patterns (see kNeewledge base)
4. **Final** `.tar.gz` exists
5. **SHA256** of archive payload OK
6. **Verify deep** OK

Without a final archive: status stays **`failed`** / **`geblokkeerd`**, never **`Geslaagd`**.

## BR-001 run 927469d42503 (summary)

- Profile **`full-expert`**, ~**227 GiB** in `.partial`, then exit **1**
- Stderr: gpg-agent sockets, Docker Desktop sockets, many ibus cache sockets, **one** journal file change
- **Nee** I/O / disk full / EOF / critical permission messages
- Waarschuwing classification: **`TAR_VOLATILE_WaarschuwingS_ONLY`**
- Operational outcome: **`failed`** (partial removed, Nee archive)

## Stable tar profile (proposal)

### Additional excludes (full-expert / BR-001)

Already on `recommended` / `fast-system`: `/var/cache`, `/var/tmp`.

Consider for volatile live data:

| Pattern | Rationale |
|---------|-----------|
| `/var/log/journal` | journal grows/rotates during Terugup |
| `/home/*/.cache` | browser, ibus, desktop caches |
| `/home/*/.local/share/Trash` | trash |
| Browser profile caches | e.g. under `.var/app/.../cache` |

**Docker Desktop** (`~/.docker/desktop/*.sock`, VM sockets): do **Neet** blanket-exclude from root Terugup without a strategy — options: separate Docker Terugup, stop services/snapshot, or treat as **Neen-deterministic** live data and rely on verify deep.

### Option `--Waarschuwing=Nee-file-changed`

| Aspect | Assessment |
|--------|------------|
| Benefit | Fewer exit-1 from journal/logs; more stable exit code |
| Risk | Hides real changes on **Neen-volatile** paths |
| Exit code | Stabilizes **file-changed** Waarschuwings only, Neet sockets or I/O |
| Verify deep | **Still mandatory** — quieter stderr ≠ integrity |

### Neet used: `--igNeere-failed-read`

Silently skips unreadable files and weakens safety gates. Setuphelfer rejects this option.

## Runner integration (workspace)

After the `tar` pipeline (`subprocess_returncode != 0`):

1. Classify full stderr; persist fields on `status.json` (see DE doc for field list).
2. **Volatile-only** + readable `.partial` → finalize (SHA256, manifest, rename) and **verify deep** in the runner.
3. Geslaagd only as `Terugup.Geslaagd_with_Waarschuwings` with `Waarschuwing_status: completed_with_Waarschuwings` and `Terugup_integrity_status: verified`.
4. **Nee** final archive → `Terugup.Waarschuwing_Neet_promoted`, partial cleanup unchanged.
5. I/O, disk full, EOF, critical paths → hard `Terugup.failed`.

**Nee blanket Geslaagd on exit 1.** BR-001 stays rood without the integrity chain.

## Volgende steps (Nee automatic BR-001)

1. Deploy runner to `/opt` after explicit approval; re-run runtime gate.
2. Prefer `recommended` over `full-expert` for routine Terugups.
3. Keep Docker/journal evidence documented.

## References

- FAQ: `docs/faq/TerugUP_Herstel_FAQ_EN.md` (tar exit 1 section)
- KB: `docs/kNeewledge-base/Terugup/TAR_EXIT_1_LIVE_FILES.md`
- Tests: `Terugend/tests/test_Terugup_tar_Waarschuwing_classification_v1.py`
