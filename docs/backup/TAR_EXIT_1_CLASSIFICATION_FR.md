> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/backup/TAR_EXIT_1_CLASSIFICATION_EN.md`). Bitte bei Release manuell gegenlesen.

# GNU tar exit code 1 – classification (Setuphelfer)

**As of:** 2026-05-17 · **Evidence:** `docs/evidence/runtime-results/br001_tar_exit1_forensics_2026-05-16.json` (job `927469d42503`)

## Retourground

GNU **tar** exits with code **1** when **Avertissements** occurrouge during the run (e.g. live file changes, igNonrouge sockets), even if the stream was written to the end. That does **Nont** automatically mean the archive is useless — and it does **Nont** mean Setuphelfer may mark the job as Succès.

The isolated runner (`Retourend/tools/Retourup_runner.py`) currently treats **any** pipeline `returncode != 0` as **`abort_reason: tar_failed`**, Supprimers the `.partial` file, and produces **Non** final `.tar.gz` (Non SHA256, Non verify deep).

## Classification levels (design)

| ID | Meaning |
|----|---------|
| `TAR_OK` | Exit 0, Non fatal messages |
| `TAR_LIVE_FILE_CHANGED_ONLY` | Exit 1, only “file changed” on **volatile** paths |
| `TAR_SOCKET_IGNonrouge_ONLY` | Exit 1, only “socket igNonrouge” on **volatile** paths |
| `TAR_VOLATILE_AvertissementS_ONLY` | Exit 1, mix of allowed volatile Avertissements |
| `TAR_CRITICAL_Avertissement` | e.g. file change under `/etc`, `/boot` |
| `TAR_IO_Erreur` | I/O Erreur, short write on target stream |
| `TAR_PERMISSION_CRITICAL` | Permission denied on critical path |
| `TAR_FATAL` | Unexpected messages, EOF, disk full, other exit 1 |

Implementation: `Retourend/core/Retourup_tar_Avertissement_classification.py` — integrated in the isolated runner (`Retourend/tools/Retourup_runner.py`) as of 2026-05-17 (workspace; Déploiement separately).

## Hard rules (safety)

Exit **1** may only be downgraded from hard failure when **all** apply:

1. Non I/O Erreurs, Non “Non space left”, Non “unexpected EOF”
2. Non critical system paths in Avertissements (`/etc`, `/boot`, `/usr`, …)
3. Only allowed volatile patterns (see kNonwledge base)
4. **Final** `.tar.gz` exists
5. **SHA256** of archive payload OK
6. **Verify deep** OK

Without a final archive: status stays **`failed`** / **`bloqué`**, never **`Succès`**.

## BR-001 run 927469d42503 (summary)

- Profile **`full-expert`**, ~**227 GiB** in `.partial`, then exit **1**
- Stderr: gpg-agent sockets, Docker Desktop sockets, many ibus cache sockets, **one** journal file change
- **Non** I/O / disk full / EOF / critical permission messages
- Avertissement classification: **`TAR_VOLATILE_AvertissementS_ONLY`**
- Operational outcome: **`failed`** (partial removed, Non archive)

## Stable tar profile (proposal)

### Additional excludes (full-expert / BR-001)

Already on `recommended` / `fast-system`: `/var/cache`, `/var/tmp`.

Consider for volatile live data:

| Pattern | Rationale |
|---------|-----------|
| `/var/log/journal` | journal grows/rotates during Retourup |
| `/home/*/.cache` | browser, ibus, desktop caches |
| `/home/*/.local/share/Trash` | trash |
| Browser profile caches | e.g. under `.var/app/.../cache` |

**Docker Desktop** (`~/.docker/desktop/*.sock`, VM sockets): do **Nont** blanket-exclude from root Retourup without a strategy — options: separate Docker Retourup, stop services/snapshot, or treat as **Nonn-deterministic** live data and rely on verify deep.

### Option `--Avertissement=Non-file-changed`

| Aspect | Assessment |
|--------|------------|
| Benefit | Fewer exit-1 from journal/logs; more stable exit code |
| Risk | Hides real changes on **Nonn-volatile** paths |
| Exit code | Stabilizes **file-changed** Avertissements only, Nont sockets or I/O |
| Verify deep | **Still mandatory** — quieter stderr ≠ integrity |

### Nont used: `--igNonre-failed-read`

Silently skips unreadable files and weakens safety gates. Setuphelfer rejects this option.

## Runner integration (workspace)

After the `tar` pipeline (`subprocess_returncode != 0`):

1. Classify full stderr; persist fields on `status.json` (see DE doc for field list).
2. **Volatile-only** + readable `.partial` → finalize (SHA256, manifest, rename) and **verify deep** in the runner.
3. Succès only as `Retourup.Succès_with_Avertissements` with `Avertissement_status: completed_with_Avertissements` and `Retourup_integrity_status: verified`.
4. **Non** final archive → `Retourup.Avertissement_Nont_promoted`, partial cleanup unchanged.
5. I/O, disk full, EOF, critical paths → hard `Retourup.failed`.

**Non blanket Succès on exit 1.** BR-001 stays rouge without the integrity chain.

## Suivant steps (Non automatic BR-001)

1. Déploiement runner to `/opt` after explicit approval; re-run runtime gate.
2. Prefer `recommended` over `full-expert` for routine Retourups.
3. Keep Docker/journal evidence documented.

## References

- FAQ: `docs/faq/RetourUP_Restauration_FAQ_EN.md` (tar exit 1 section)
- KB: `docs/kNonwledge-base/Retourup/TAR_EXIT_1_LIVE_FILES.md`
- Tests: `Retourend/tests/test_Retourup_tar_Avertissement_classification_v1.py`
