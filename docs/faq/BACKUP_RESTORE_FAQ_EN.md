# FAQ – Backup & Restore – English

## Do I need a green backend version gate before backup/restore tests?

**Yes.** If **`GET /api/version`** does not return **HTTP 200** with **`status":"success"`**, or production **`config/version.json`** does not match the approved schema, results are not trustworthy. Run **`scripts/check-backend-version-gate.sh`** and the update runbook (`docs/operations/BACKEND_UPDATE_RUNBOOK_EN.md`) first — **no** backup job while `blocked_update_required`.

## Why is full-root backup slow and why does it not scale with many CPU cores?

**gzip** (and classic **`tar -czf`**) compresses mostly **single-threaded**. Many cores barely help; **I/O** and **one CPU** often cap throughput. **pigz** uses multiple threads while staying **gzip-compatible** (faster when installed). **zstd** is faster/scales better but needs an **end-to-end** pipeline including finalize/manifest — until then the product stays **gzip-compatible**. **Full root** is intentionally an **expert/long-run** path; for daily use and Raspberry Pi prefer **smaller profiles** (see **`docs/backup/BACKUP_PERFORMANCE_EN.md`**, profile overview **`docs/backup/BACKUP_PROFILES_EN.md`**, matrix **BR-016**, **BR-019**).

## Which profiles does the UI offer?

The default is **“Recommended backup”** (`recommended`). **Expert mode / full root** (`full-expert`) is separated visually and needs a confirmation checkbox; legacy API `type: full` behaves like **full-expert** with warnings. Details and API: **`docs/backup/BACKUP_PROFILES_EN.md`**, endpoints `/api/backup/profiles` and `/api/backup/profile-preview`.

## What about progress, ETA, and evidence?

The runner fills **`progress_optional`** (phase, throughput, **`eta_seconds`** only with a reliable estimate, otherwise **`null`**). After job end an **evidence bundle** can be collected (logs, `systemctl`, `journalctl` excerpts, mounts) — see **`docs/backup/BACKUP_EVIDENCE_COLLECTOR_EN.md`** (**BR-017**). UI copy lives under **`backup.messages.*`** in locales (slow but active, compression bottleneck, package blocker, ETA).

## Why must the backup not be stored on the root filesystem?

A backup stored on the same filesystem as the running system is unsafe. A disk failure, user error, or restore problem may destroy both the original system and the backup.

## Why was `/mnt/setuphelfer/backups` blocked?

The path was located on the root filesystem and was not a separate safe target device. The storage protection logic correctly blocked it.

## Why was `/media/...` initially blocked?

The previous logic blocked `/media` globally. This was too strict because Linux desktop systems typically mount external drives below `/media/<user>/...`.

## How was this fixed?

`/media` was not globally allowed. A target below `/media` is only accepted if it resolves to a real, safe block device and is not a system, boot, Windows, or EFI partition.

## Which external media does Setuphelfer prefer for backups?

Backups should live on **external media**, not the root/boot/system drive. Priority (highest first): **external NVMe**, **external SSD**, **external HDD**, **USB flash drive**, **SD card**. Internal NVMe hosting `/` and other internal-only paths are unsuitable. See `docs/backup/BACKUP_TARGET_POLICY_EN.md` and `docs/knowledge-base/backup/BACKUP_TARGET_SELECTION.md`.

## What does the strategic path `/media/setuphelfer/setuphelfer-back` mean?

This is a **documented conventional path** that may be used **only** if it truly resides on the **selected external volume** (mount source is an external `/dev/...`, not the root filesystem). Setuphelfer does **not** create it automatically, does **not** format disks, and does **not** relocate existing mounts. If your volume is already mounted elsewhere (e.g. `/media/<user>/setuphelfer-back`), there is **no** automatic rewrite — that requires **explicit operator approval** (mount/bind/policy).

## What if Setuphelfer cannot traverse or write the target?

There is **no** silent fallback to internal space. With the current workspace backend, the API reports **`backup.target_traverse_denied`** with diagnosis **STORAGE-PROTECTION-006**. The operator/user must fix permissions/mounts.

## Why does Setuphelfer not auto-format or partition?

Existing data on external media must be preserved. Without a clearly safe external target, backup stays **blocked**.

## Why must `/media` be excluded from full backups?

When backing up `/`, including `/media` would also include external drives. This can lead to huge backups, recursive backup runs, or stalls.

## Which paths are excluded from full backups?

At least:

- `/proc`
- `/sys`
- `/dev`
- `/tmp`
- `/run`
- `/mnt`
- `/media`
- `/run/media`
- the specific backup target path

## Why did the backup stall?

The specific run stalled at approximately 27.46 GB. Probable causes were:

- backup source scope too broad, including `/media`
- possible pipe blocking through tar stdout/stderr

## What was changed?

- `/media` and `/run/media` were added as excludes.
- stdout is no longer buffered.
- stderr is consumed while the process is running.

## What still needs to be done after the fix?

A new full-backup run must complete successfully. Manifest, Basic Verify, and ideally Deep Verify must then be checked.

## When is monolith refactoring allowed?

Only after:

- target check succeeds
- full backup succeeds
- manifest exists
- verify succeeds

## Why does deep verify fail with “integrity” or symlink-related messages?

Deep verify applies strict checks (including symlinks and staging containment). **Full-root archives** may contain absolute symlink targets or members that appear to “escape” the staging root, which can yield `backup.verify_integrity_failed` even when the storage medium is healthy. Mitigation: validate context, use basic verify where appropriate, and read `docs/knowledge-base/BACKUP_VERIFY_PREVIEW_RUNTIME.md` (diagnosis id `VERIFY-STAGING-038`).

## Why does restore preview fail with “No space left on device” while the backup disk has free space?

Preview extraction runs under **`/tmp`** or the backend’s effective **`TMPDIR`**, often inside **PrivateTmp**. A small **tmpfs** or a full service `/tmp` causes **ENOSPC** even when `/mnt/...` is large. Mitigation: set **`TMPDIR`** via a systemd drop-in to a large persistent path, restart the service. See `docs/knowledge-base/BACKUP_VERIFY_PREVIEW_RUNTIME.md` and diagnosis `RESTORE-TMPFS-007`.

## Why does the backend die with OOM or cgroup kills during verify/preview?

A small **`MemoryMax`** (or tight swap limits) on **`setuphelfer-backend.service`** caps RAM for the process; large archives can exceed it quickly. Mitigation: raise **`MemoryMax`** / **`MemorySwapMax`** in a unit drop-in, `daemon-reload`, restart the service. See `docs/knowledge-base/BACKUP_VERIFY_PREVIEW_RUNTIME.md` and diagnosis `SYSTEMD-MEMORYMAX-037`.

## What does Inspect detect in phase 0/1?

Inspect collects raw read-only data: block devices, filesystems, mount status, UUID conflicts, boot status, and network status.
The data is available via `GET /api/inspect/run`.

## Why does Inspect not repair anything yet?

Phase 0/1 is intentionally defensive and read-only. It does not perform write operations on target media.

## Why is Windows only detected but not modified?

Inspect only exposes hint flags (for example `possible_windows`, `possible_dualboot`) and does not run partitioning, bootloader, or restore actions.

## Why are there no action recommendations yet?

Phase 0/1 focuses on stable data collection and structured codes only. Scoring, traffic-light decisions, and recommendations are explicitly out of scope.

## What does Inspect add in phase 2?

Phase 2 extends `GET /api/inspect/run` with `classification` (system type, confidence, indicator codes, risk level) and `advice` (recommended paths as **codes** with priority). It still does **not** start repair, restore, or deploy steps.

## Why can system classification be wrong?

Classification only uses **already collected** raw data (e.g. detected filesystem types, boot codes). Missing disks, rescue-only views, or NTFS data partitions without a full Windows install can yield **UNKNOWN** or **PARTIAL_SYSTEM** — by design.

## Why is Windows not repaired automatically?

Inspect performs **no** writes and **no** bootloader/partitioning actions. Windows-like classification is **interpretation**, not authorization to change the system.

## Why is advice not an action?

`advice.recommended_paths` are **structured hints** for humans or external workflows (`requires_confirmation` reflects “do not auto-run”). The UI lists these codes **without** triggering buttons.

## Why can’t I select my disk (write safety)?

The UI only shows **status** from Inspect (`write_safety_summary` / `GET /api/safety/targets`). If a disk is **blocked** (e.g. system disk, dual-boot pattern, ambiguous NTFS), there is **no** bypass button — by design.

## Why is “Windows” blocked?

**NTFS-only** or Windows-like layouts without a clear **backup-candidate** pattern yield **`SAFETY_WINDOWS_DETECTED`** — writes are **not** auto-approved.

## Why is there no override in phase 1?

Write safety returns **codes** and flags (`requires_override` documents future workflows only). There is **no** UI to bypass locks in this phase.


## Why do we back up again before restore/deploy?

Preflight backup is the final defensive snapshot before later interventions. It provides a fallback point if subsequent steps fail.

## Why do I need confirmation?

`/api/preflight/backup/execute` only accepts a plan-bound `confirmation_token` issued by `preview`. No token means no execution.

## Why can't I back up to any disk?

Write safety blocks risky targets (system disks, live media, Windows/dual-boot risk, unknown devices). Preflight strictly respects those blocks.


## Why is there preview first?

The rescue orchestrator validates safety, verify and dry-run first. This minimizes risk before any real write-back could be allowed.

## Why is restore not executed yet?

Phase 1 exposes only `POST /api/rescue/preview`. No new execute endpoint is included at this stage.

## Why does safety block my target?

System/live/Windows/dual-boot/unknown targets remain hard-blocked.

## Why is preflight recommended?

If no matching preflight plan is known, the preview reports a warning (`RESCUE_PREFLIGHT_RECOMMENDED`).


## Why does restore require a preview session?

Execute is only allowed from a valid prior preview. Without session ID + token, execution is blocked.

## Why do I have to confirm again?

The token is session-bound and expires. This prevents global restore authorization.

## Why does Setuphelfer re-check safety and verify before execute?

State can change between preview and execute (target, mounts, backup file). Safety and verify are re-evaluated immediately before restore.

## Why is boot-repair not executed automatically yet?

Phase 2 intentionally separates file restore and boot repair. Automatic boot-repair is out of scope in this execute stage.

## Why does Setuphelfer validate again after restore?
A file restore can be technically successful while target structure or boot artifacts are incomplete. Post-restore validation therefore runs a read-only plausibility check.

## Why can restore still be successful with warnings?
Warnings indicate follow-up work (for example missing `fstab` or missing setuphelfer artifacts), but they do not always mean the restored target is unusable.

## Why is boot repair only recommended?
This phase does not execute repair actions. Missing kernel/initramfs artifacts only emit `POST_RESTORE_BOOT_REPAIR_RECOMMENDED`.

## Why is setuphelfer not auto-installed?
Post-restore validation is intentionally read-only. Missing setuphelfer artifacts are reported as warnings without automatic installation.

## Why does Setuphelfer check boot capability?
A file restore can succeed while boot artifacts are still incomplete. Boot capability adds a read-only plausibility layer.

## Why does “likely bootable” not mean guaranteed bootable?
The assessment is defensive and based on artifacts (fstab, kernel, initramfs, hints), not on an actual boot execution.

## Why are Windows/dualboot systems not auto-repaired?
Windows/dualboot scenarios are high risk and are only detected and flagged for warning/manual review.

## Why is there no boot repair button yet?
This phase is intentionally read-only. Repair actions are outside the current API scope.

## Why does Setuphelfer not auto-repair boot yet?
In this phase, Boot Repair Plan provides theoretical suggestions only. Execution is intentionally disabled.

## Why is boot repair risky?
Wrong target disk, unknown layouts, or bootloader mistakes can make systems unbootable.

## Why do I have to decide manually?
Boot repair is safety-critical. Setuphelfer therefore flags risky situations for manual review.

## Why are Windows/dualboot systems not auto-repaired?
Windows/dualboot setups carry high overwrite/conflict risk and remain manual by design.

## What is the Recovery Report?
The Recovery Report combines existing rescue outputs into one structured view (inspect, safety, preflight, preview, execute, post-restore, boot).

## Why is restore not automatically failed when warnings exist?
Warnings indicate risks or follow-up work, but not necessarily a complete technical failure.

## Why are some actions blocked?
Blocks follow safety policy (for example no restore without valid preview/token and no automatic Windows/dualboot repair).

## Why does Setuphelfer show recommendations instead of doing everything automatically?
This phase is intentionally defensive and advisory-only. Critical actions remain explicitly manual.

## Why is there no “Fix All” button?
Boot repair is risk-sensitive. Phase 2 only allows single explicit confirmed actions.

## Why are some repairs blocked?
Windows, dualboot, and high-risk cases are defensively blocked.

## Why do I need a token?
The token binds execution to one specific session, target, and action.

## Why is boot not repaired automatically?
Automatic cascades are excluded in this phase. Every repair must be confirmed individually.

## What is a recovery minimal system?
A recovery minimal system is a deliberately small target state to restore reachability (for example SSH + setuphelfer backend) — in this phase plan-only.

## Why is SSH not enabled automatically?
Automatic remote exposure is security-sensitive and remains manual.

## Why is setuphelfer not installed automatically?
Phase 1 is advisory-only. Installation appears only as a required step suggestion.

## Why are Windows/dualboot targets blocked?
These layouts are high risk and are defensively excluded from automatic handling.

## Why does execute do nothing yet?
This phase only provides session and contract validation. Real step execution comes in a later phase.

## Why do I need a session?
The session binds token, target path, and selected steps together.

## Why can't I enable SSH immediately?
SSH enablement is security-sensitive and intentionally blocked in prep phase.

## What happens in the next phase?
In the next phase, tightly scoped steps can be executed under the same safety controls.

## Why is SSH still not active after phase 2b?
Phase 2b records safe preparation only. Real SSH enablement remains a separate explicit step.

## Why is only a recovery note written?
The note is a traceable low-risk baseline without direct system activation.

## Why is setuphelfer only prepared?
Only local sources are validated and prepared. Service start/enable is still disallowed.

## Why is there no automatic remote maintenance?
Automatic remote maintenance increases risk and is intentionally excluded in this phase.

## What does “Activation” mean?
In this phase, activation means a safety and sequencing plan for later reachability.

## Why is SSH not enabled automatically?
SSH enablement remains a separate explicitly confirmed step.

## Which ports are opened?
In this plan phase, no ports are actually opened. The plan only models potential exposure.

## Why is the system not reachable yet?
The activation plan is advisory-only and does not start services.

## Why does activation execute do nothing yet?
Activation execute prep validates session, token, and plan binding only. Real activation comes in the next phase.

## Why is a token required?
The token prevents unauthorized activation and binds execution to one session.

## Why is SSH still not enabled?
SSH activation is security-sensitive and explicitly excluded in this phase.

## What happens in controlled activation?
Only then are individually approved steps executed under strict safety controls.

## Why SSH key only and no password?
Password login is intentionally prepared as disabled in the target system. This keeps remote access restricted to key-based authentication.

## Why no root login?
SSH root login is a high-risk access path. Therefore `PermitRootLogin no` is prepared in target config and not relaxed.

## Why is the host system not modified?
Controlled execute writes only under `target_path`. Running host services and host accounts are left unchanged.

## Why is remote maintenance not guaranteed after this step?
This phase prepares only bounded building blocks. Actual reachability still depends on target state, networking, and manual approval.

## Why does LAN bind require explicit confirmation?
LAN bind can expose the backend port on the network. Therefore `allow_lan_backend_bind=true` is required explicitly and emits a warning code.

## When may a deploy be performed?
Only when Inspect and write-safety show an **empty** or explicitly empty-signaled target (for example `SAFETY_EMPTY_DISK` on all considered disks). Anything else stays blocked or requires manual review.

## Why is my disk blocked?
Common reasons: system disk, live media, Windows/dual-boot patterns, data-bearing partitions, or ambiguous safety signals. The deploy plan follows the same hard-stop rules.

## Why is there no automatic installation?
The deploy phase returns an advisory **plan** with codes and profiles only. Installation, partitioning, and writes are intentionally out of scope.

## Which profiles exist?
Logical suggestions (minimal Linux, web server, backup node, NAS-like, experimental) without referencing images. No profile is executed automatically.

## Why does deploy execute do nothing yet?
The current deploy execute prep phase only validates session, token, and plan/target/profile binding, then returns `DEPLOY_EXECUTE_READY`.

## Why is a token required?
The token binds authorization to one specific deploy session and prevents uncontrolled execution.

## Why must a profile be bound?
The session is tied to one concrete, suitable profile so later phases cannot silently switch profiles.

## What comes next in deploy preview?
The next phase validates concrete installation steps as preview/dry-run before any real execution can be allowed.

## Why is nothing installed yet?
Deploy Preview is a simulation and returns only a controlled preview result with codes.

## Why is remote_image not downloaded?
In this phase `remote_image` is only structurally validated (URL/checksum); download remains intentionally blocked.

## Why does preview show writing steps?
The list indicates which steps could write in later phases. Preview itself executes nothing.

## What comes after deploy preview?
After preview, a tightly controlled execute phase follows with additional approval and repeated safety checks.

## Why are images not downloaded?
The source registry is metadata-only. Downloads are intentionally disabled in this phase for safety.

## Why are some sources blocked?
Blocked sources are intentionally restricted by platform/policy or violate defensive validation rules.

## Why is architecture validated?
Wrong architecture can lead to non-bootable or non-starting systems later. Early validation reduces this risk.

## Why are there experimental sources?
Experimental sources provide transparent risk visibility and are explicitly marked as high risk.

## Why does Setuphelfer not download an image yet?
The cache-plan phase is planning-only. Downloads are intentionally not started yet for safety.

## Why is a checksum required?
Without an expected checksum, image integrity cannot be validated defensively.

## Why are internal URLs blocked?
Internal/localhost URLs carry misuse and misconfiguration risk and are therefore blocked in this phase.

## Why is cache only planned?
This keeps all steps transparent and reviewable before a controlled execution phase is allowed.

## Why local images only?
This phase is intentionally local-only to avoid uncontrolled remote fetches.

## Why is checksum verified?
When an expected hash is provided, local file integrity is verified before cache readiness.

## Why is the image not mounted?
Mount/extract is not allowed at this safety level; only file validation and controlled copy are performed.

## Why are arbitrary cache paths not allowed?
Writes are restricted to allowed Setuphelfer cache prefixes to prevent path abuse and traversal.

## Why is the image not mounted?
Deploy Image Inspect is intentionally limited to read-only file metadata checks. Mount/loop/extract is excluded in this phase for safety.

## Why is file extension not enough as a security proof?
An extension is only a naming hint and does not prove integrity or origin. Therefore optional SHA256 verification is used and uncertain states are handled defensively.

## Why is architecture not guaranteed?
Without image content analysis, architecture cannot be determined reliably. The API therefore returns `DEPLOY_IMAGE_ARCHITECTURE_UNVERIFIED`.

## Why must the image be inside Setuphelfer cache?
Only approved cache paths are allowed for later deploy flows. This reduces path abuse risk and blocks unchecked external paths.

## Why is nothing written yet?
Deploy Write Plan is intentionally simulation-only. Disk writing, partitioning, and formatting remain disabled in this phase.

## Why is target confirmation required multiple times?
Multiple confirmations reduce operator error in destructive follow-up phases. Target, data-loss acceptance, and final approval are gated separately.

## Why are Windows/dualboot layouts blocked?
Windows/dualboot layouts carry high risk of data loss and boot conflicts. The safety logic therefore hard-blocks these scenarios.

## What happens after write plan?
After a successful write plan, a later separately approved execute phase can follow, with repeated safety re-checks.

## Why is nothing written yet?
The current deploy write execute phase is a dry-run contract. It validates session, token, and re-check gates and returns simulated steps only.

## Why are so many confirmations required?
Confirmations are intentionally redundant so target device, data-loss acceptance, and image source cannot be approved accidentally.

## Why is the target checked multiple times?
Context can change between plan, session, and execute. The dry-run therefore revalidates target binding immediately before simulated execution.

## What happens in the real write phase?
A future real write phase must be approved separately and is out of scope for this dry-run contract.

## Why is there another confirmation step?
The final confirmation step reduces operator mistakes immediately before any future real-write phase and enforces explicit final approvals.

## Why snapshot/fingerprint?
Snapshot and fingerprint bind approval to a concrete target signature derived from existing data and make silent target drift detectable.

## Why is nothing still written?
Final confirmation remains a pure dry-run gate. It validates consistency and acknowledgements without disk access.

## What follows after final confirmation?
A later separately approved phase can then prepare an actual write flow.

## Why are real disks still not written?
The test harness is intentionally isolated and allows test files only. Real blockdevice write paths stay blocked.

## Why test files only?
This verifies write logic safely without risking production disks.

## Why is max_bytes limited?
The byte limit reduces risk and keeps test scope bounded to controllable size.

## What follows after the test harness?
After stable harness validation, a later production write phase can be planned and approved separately.

## Why is there still no real writing?
The real write guard is intentionally only a safety and approval layer without any write engine.

## Why removable only?
Non-removable targets carry higher system-disk mis-target risk and are therefore hard-blocked.

## Why harness proof required?
Without a successful isolated harness proof, real-write preparation is fail-closed blocked.

## Why snapshot/fingerprint?
The fingerprint binds approval to a concrete target state and detects drift between session and check.

## Why no system disks?
System disk, Windows, dualboot, LVM, RAID, and loop scenarios remain strictly blocked in this phase.

## Why USB/SD only?
The hardware gate marks only removable test media with matching transport as potentially test-ready.

## Why no internal drive?
Internal/non-removable drives are defensively blocked to reduce mis-target risk in later destructive phases.

## Why operator checks?
Physical cross-checks reduce mix-ups that software-only signals cannot safely eliminate.

## Why is physical control necessary?
Devices may be replugged, replaced, or newly mounted between steps; manual end-check remains required.

## Why still no real writing?
This phase only provides gate and protocol information. A real write engine is still absent.

## Is there any real writing now?
Only the **real-write prototype** (`POST /api/deploy/write/prototype`): strictly limited, feature-flagged, removable USB/SD only, 512MB cap, pure Python I/O with verification. Not a full installer and not a general write endpoint.

## Why removable media only for the prototype?
Mis-targeting internal system disks is harder to rule out operationally; the prototype stays on removable test media.

## Why a 512MB limit in the prototype?
Limits blast radius and runtime for first real write tests; larger images are intentionally out of scope.

## Why no `dd` in the prototype?
Shell tools are harder to audit (failure modes, privileges, unexpected flags). Pure Python I/O is straightforward and subprocess-free.

## Why no Windows/dualboot targets?
These remain blocked by the safety chain (inspect/safety/hardware gate) to reduce data-loss risk on mixed layouts.

## Why not a full installer after the prototype?
The prototype performs a raw copy of a single image up to the cap; there is no partitioning, boot loader setup, or unattended install—that would be a separate, explicitly approved phase.

## Why no retry in the real-write prototype?
Retries would mask real failures (wrong target, drift, partial writes) and increase risk; the pipeline is intentionally fail-hard.

## Why immediate abort on drift?
Media state can change between gate and write (mount, read-only, path). Aborting immediately avoids writing against an invalid context.

## Why is device drift critical?
The fingerprint and live signals (mount, RO, size) must match the approved snapshot; otherwise mis-target or corruption risk rises.

## Why is verification strict?
Verification compares exactly the written byte count with no silent repair; mismatches or short reads yield a clear error code.

## What are the failure-injection hooks?
Only with `SETUPHELFER_REAL_WRITE_TESTMODE=1`: controlled simulation env vars (`FAIL_BEFORE_OPEN`, `FAIL_AFTER_OPEN`, `FAIL_AFTER_CHUNKS`, `FAIL_VERIFY_MISMATCH` + path, `FAIL_DURING_FSYNC`, `FAIL_DEVICE_CHANGED`). See `docs/deploy/DEPLOY_REAL_WRITE_FAILURE_INJECTION_EN.md`.

## Why a separate deploy write runner instead of running the backend as root?
The backend stays unprivileged; a small one-shot runner can later gain elevated rights only for block-device I/O without widening the whole API surface.

## What is the deploy write job file?
A local JSON with `job_hash` binding (SHA256 over canonical data excluding the hash field), target device, image path/checksum/size, guard metadata, and fixed constraints. See `docs/deploy/DEPLOY_WRITE_RUNNER_CONTRACT_EN.md`.

## What does the runner do in this phase?
`--dry-run` only: load job, validate, print JSON to stdout — no device open, no writes. CLI: `backend/tools/deploy_write_runner.py`.

## Why is sudoers risky for the runner?
Every `NOPASSWD` rule increases blast radius if the account is compromised; wildcards in the sudoers line and permissive `env_keep` can enable argument or library injection (`PYTHONPATH`, `LD_PRELOAD`). Prefer fixed paths, minimal environment — see `docs/evidence/DEPLOY_WRITE_RUNNER_RUNTIME_VALIDATION.md`.

## Why one-shot instead of a root backend or daemon?
A short-lived process handling a single job reduces exposed state and attack surface; a permanently root backend or privileged daemon would combine network/session risk with elevated privileges.

## Why lock files for the deploy runner?
An exclusive per-job lock file prevents parallel double execution for the same job; stale detection (PID/TTL) avoids indefinite blocks after a crash. See `docs/deploy/DEPLOY_RUNNER_LIFECYCLE_EN.md`.

## Why a lifecycle state machine?
Explicit phases and terminal states make behavior auditable and prevent silent “jumps” (fail-closed). Transitions are enumerated; illegal ones are rejected.

## Why an audit log (JSON Lines)?
A traceable event sequence without secrets (no full checksums/tokens in each line); supports operations and post-mortems. Directory `runner-audit/`.

## Why stale lock cleanup?
Without cleanup, an orphaned lock could block real operations after the process exits; cleanup removes dead or TTL-expired locks in a controlled way.

## Why TOCTOU rechecks?
Between validation and a (future) write, media, mounts, or metadata may change; repeated read-only comparisons before critical steps narrow the inconsistency window.

## Why a separate backend-to-runner handoff?
It keeps the backend unprivileged and passes only a tightly defined dry-run job to the isolated runner; no free-form shell commands and no direct device access in backend flow.

## Why job files for handoff?
Job files are auditable, hash-bound, and locally re-validatable. The runner can independently re-check the exact same input (fail-closed) before any future privileged step.

## Why atomic write?
`.tmp` + rename avoids half-written job files on crash/interruption and reduces race/TOCTOU risk while the runner reads the file.

## Why dry-run runner in handoff?
It validates the full create->start->JSON-response pipeline without performing real device actions.

## Why is `subprocess.run` allowed here?
Only to invoke the local one-shot runner with fixed args, `shell=False`, controlled `cwd`, minimal environment, and timeout. No free command execution.

## Why no automatic sudoers installation?
Automatic sudoers edits are high-risk and hard to roll back safely. The boundary phase therefore provides a read-only policy model instead of system modification.

## Why fixed runner paths?
Absolute, stable paths reduce PATH/symlink manipulation risk and prevent launching a different interpreter or script.

## Why block PYTHONPATH?
`PYTHONPATH` can redirect imports to attacker-controlled modules. The boundary audit marks it as critical.

## Why is LD_PRELOAD dangerous?
`LD_PRELOAD` can inject arbitrary code before program startup and bypass assumptions; it is treated as blocking.

## Why no real root sandbox in this phase?
This phase is intentionally simulated: policies are modeled and tested without real privilege transitions or system changes, keeping risk tightly controlled.

## Why no real signals?
Signal behavior is represented as a model (`would_send_signals`) to avoid unintended termination of unrelated or long-running local processes.

## Why disable stdin?
A non-interactive one-shot runner should not depend on runtime input; disabling stdin reduces interaction and injection surfaces.

## Why a minimal environment?
A small inherited environment lowers loader/interpreter variable abuse and reduces PATH ambiguity.

## Why a one-shot runner?
Short-lived execution with fixed input/output and no background mode reduces zombie/orphan risk and uncontrolled state accumulation.

## Why no root backend?
A root-running backend dramatically widens attack surface. The plan enforces a later, minimal one-shot runner with a strict privilege boundary.

## Why no permanent runner service?
A long-lived privileged daemon increases persistence and attack risk. The model stays one-shot and non-listening.

## Why is sudoers only planned?
Sudoers changes are highly sensitive; this phase keeps them as audit/plan text only, with no installation or execution.

## Why is manual installation required?
Path/ownership/permission checks are security-critical and must be reviewed on the target host; automatic apply remains intentionally disabled.

## What should rollback look like?
Rollback should be documented: remove snippets, revert directory permission decisions, and re-verify dry-run behavior before proceeding.

## Why a dry-run validator only?
This phase validates readiness and security boundaries only. It keeps risk low before any later manual privileged steps are performed.

## Why no visudo in the validator?
The validator is fully read-only and checks only provided snippet text. System-level verification/installation remains a separate manual task.

## Why are missing paths only review_required?
Missing target paths often mean "not yet manually prepared". That is a review concern as long as no hard security violation is detected.

## Why is rollback mandatory?
Privileged integrations need a clear rollback path so misconfigurations can be reverted quickly and reproducibly.

## Why blueprint only?
The blueprint separates planning from execution: paths, permissions, and boundaries are modeled first without system changes.

## Why no automatic package?
Automatic packaging/installation can roll out mistakes at scale. This phase is intentionally limited to manifest and review.

## Why is sudoers not installed automatically?
Sudoers is highly sensitive; installation remains a manual controlled step with separate approval.

## Why include rollback in the manifest?
Rollback must be defined from day one so reversions stay reproducible and auditable.

## Why is post-install validation mandatory?
After manual setup, dry-run validation plus renewed runtime proof is required to confirm no security assumption regressed.

## Why run a consistency audit?
Multiple planning layers reduce risk only if they encode the same security contract; consistency checks catch contradictions early.

## Why must paths match across all layers?
Diverging runner/job/sudoers paths create bypass risk and make approvals unreliable.

## Why align rollback steps?
An incomplete rollback path can leave systems in an unsafe intermediate state; mandatory rollback codes must stay aligned.

## Why are validation steps non-automatic?
Validation remains a controlled manual security process; automation could silently carry forward wrong assumptions.

## Why not production-ready yet?
Critical hardware and privileged-runtime validations are still open, so release status stays below production approval.

## What does ready_for_lab mean?
`ready_for_lab` means controlled lab/test usage is acceptable, while production real-write approval remains blocked.

## Why do hardware E2E gaps block release?
Without strong hardware E2E evidence, real media/timing failure risk remains too high.

## Why is a sudoers runtime test required?
Policy text alone is insufficient; runtime proof is required to confirm path/environment boundaries in the target setup.

## Why is hardware failure-injection still required?
Only real hardware reproduces hotplug, reenumeration, and race behavior reliably; simulation alone does not fully cover these classes.

## Why create a lab plan before further implementation?
The plan prioritizes critical evidence first and reduces risk through explicit manual gates.

## Why enforce a fixed order?
The order minimizes misinterpretation: policy/dry-run checks first, hardware-heavy scenarios next, rollback validation last.

## Why only one test medium?
A single clearly labeled medium significantly lowers mis-targeting and mix-up risk.

## Why include an operator stop condition?
Operator uncertainty is itself a safety signal; testing must stop immediately when confidence is lost.

## Why no automatic test run?
Hardware-adjacent safety validation requires controlled manual observation and on-site decisions.

## Why must sudoers runtime testing be planned?
Only a structured test design can validate policy assumptions, environment boundaries, and dry-run behavior reproducibly.

## Why is sudo not run automatically?
Automatic privileged execution is intentionally forbidden in this phase; execution remains a later controlled manual task.

## Why is visudo manual only?
Syntax/policy verification is safety-critical and should run under direct local operator control.

## Why are negative sudoers tests necessary?
Negative cases prove fail-closed behavior against unsafe patterns like env_keep, wildcards, and generic invocations.

## Why must privileged validation be planned?
This step links sudoers, runtime, lifecycle, and audit evidence into one coherent dry-run verification path before any future real-write approval.

## Why is no real root runner started anyway?
This phase remains test-design and review only; real privileged execution is intentionally excluded.

## Why is --dry-run mandatory?
Enforced dry-run validates privileged control paths without introducing device-write risk.

## Why must UID/GID be documented?
UID/GID evidence proves the effective runner context and whether the intended privilege boundary would hold.

## Why are negative tests required before real write?
They demonstrate fail-closed behavior for hash, path, environment, and lock failures before touching real media.

## Why is the first real write only planned?
The first hardware E2E write is high-risk, so it is modeled first as a controlled and auditable manual plan.

## Why disposable media only?
Only disposable media limits potential impact if anything unexpected occurs despite safeguards.

## Why is SHA256 verification mandatory?
Verification proves end-to-end data integrity and prevents silent continuation after a faulty write.

## Why no retry after verify mismatch?
A mismatch is a hard safety signal; retries without root-cause analysis can hide serious issues.

## Why not claim automated recovery?
Automated recovery can mask side effects. The plan instead requires transparent manual follow-up and documentation.

## Why is failure injection on real hardware required?
Only real hardware exposes timing, media, and state transitions realistically enough to validate failure paths with confidence.

## Why run each failure case individually?
Isolated runs avoid overlapping effects and keep root-cause/evidence interpretation clear.

## Why is retry after failure not allowed?
Retries without analysis can hide inconsistent states; state must be reassessed first.

## Why must media be re-evaluated after a failure?
After failures, media state may be uncertain; safe continuation requires a fresh gate/state check.

## Why not claim automated repair?
Automated repair risks silent side effects. The process is intentionally manual and auditable.

## Why is device reenumeration dangerous?
During reenumeration, the same media may appear under a new path, or a different media may reuse the old path.

## Why is /dev/sdb not stable enough?
Kernel device names can change after reconnect/order changes and are not a reliable identity signal by themselves.

## Why compare fingerprint and realpath?
The combined check reduces confusion between path churn and actual media identity changes.

## Why no retry after device change?
A device change breaks core safety assumptions and requires fresh preconditions, not immediate retry.

## Why do multiple similar USB media block tests?
Identity ambiguity is a high-risk mis-targeting condition and must fail closed.

## Why are hotplug race tests necessary?
Race conditions are timing-sensitive and can violate guard/lifecycle assumptions unless explicitly validated.

## Why are unexpected mounts dangerous?
Unexpected mount changes can invalidate target identity and safety assumptions, so they must fail closed.

## Why is lock cleanup mandatory after abort?
Stale locks block follow-up validation and can cause inconsistent state interpretation.

## Why no retry after a race abort?
Race aborts indicate unstable state; retry without fresh reassessment is unsafe.

## Why run each race case individually?
Isolated cases provide clear causality between trigger and observed abort/block behavior.

## Why are rollback runtime tests necessary?
They verify that abort/failure paths clean up safely without leaving risky or inconsistent residual artifacts.

## Why must audit data never be deleted?
Audit data is required for safety evidence and traceability; it may be archived/marked, but not removed.

## Why no recursive deletion without prefix checks?
Without strict prefix boundaries, cleanup can drift into unintended paths and damage system data.

## Why are symlinks dangerous in cleanup?
Symlinks can silently redirect cleanup to foreign locations and bypass intended safety boundaries.

## Why are system paths off-limits?
`/etc`, `/opt`, and productive `/var/lib` areas must never be modified by this test design.

## Why is test-design-ready not lab-ready?
Test-design-ready only means plans are complete; runtime evidence from real executions is still missing.

## Which runtime tests are still missing?
All seven manual runtime executions: sudoers runtime, privileged validation, real-write E2E, failure injection, reenumeration, hotplug race, and rollback runtime.

## Why can plan docs not replace runtime evidence?
Documentation defines intended behavior but does not prove real runtime behavior under actual conditions.

## Why is there no automatic approval?
Approval requires controlled manual runtime evidence; automation is not suitable at this safety level.

## Why create a central runbook bundle?
A central bundle prevents gaps between individual plans and provides a consistent, traceable execution framework.

## Why enforce a fixed sequence?
The sequence reduces cascading risk and ensures later steps depend on validated prerequisites.

## Why include an operator checklist?
Critical safety prerequisites are explicitly acknowledged instead of assumed.

## Why no automatic execution?
Hardware runtime checks require contextual human decisions and controlled stop criteria.

## Why separate evidence per runbook?
Each runbook has distinct risk and acceptance criteria; separate evidence is required for clear traceability.

## Why create a runbook export?
The export makes manual execution reproducible by keeping all required artifacts centralized and versioned.

## Why provide an evidence template?
A shared template reduces omissions and improves comparability across runbook runs.

## Why include a JSON schema?
The schema enforces required result fields and supports consistent evaluation.

## Why no automatic test execution?
Runtime steps intentionally remain manual because hardware state and safety decisions require contextual judgment.

## Why restrict to docs/evidence paths only?
Exports must not touch system paths; this keeps installation and runtime environment unchanged.

## Why validate runtime result files?
Validation keeps manual lab evidence structured, comparable, and fail-closed before any acceptance decision is recorded.

## Why validate runbook sequence?
Later hardware/rollback steps must depend on validated prerequisites; out-of-order results break safety assumptions.

## Why does missing evidence block?
Missing proof prevents reliable safety assessment (for example mount/verify/audit state) and must therefore be blocking.

## Why is lab_ready_candidate not an automatic approval?
`lab_ready_candidate` is only a manual acceptance decision after full evidence review, not an automatic execution trigger.

## Why is path protection required for result ingestion?
Without a strict allowed root, foreign paths, symlinks, or traversal could be read unintentionally and bypass safety boundaries.

## Why is lab_ready_candidate not a production approval?
`lab_ready_candidate` only indicates a controlled lab state. Production approval remains a separate decision with additional safety and operational evidence.

## Why do residual risks stay visible?
Even with successful lab runbooks, residual uncertainties remain (scope limits, host/media coverage, operator factors) and must stay transparent.

## Why is operator decision always required?
Acceptance is intentionally manual. Aggregation provides structure and evidence summaries, but does not replace accountable human approval.

## Why does a safety finding block?
Safety findings indicate broken protection assumptions (for example verify mismatch or device/mount drift) and must fail closed.

## Why is repeat_required not auto-retried?
Automatic retries can increase hardware and operator risk; repeats must be explicitly planned and manually controlled.

## Why export an acceptance report?
Export creates consistent artifacts for operator review, traceability, and later audits.

## Why is lab candidate not production approval?
Lab candidate only means current lab evidence is sufficient for lab context; production approval requires additional evidence.

## Why do residual risks stay in the report?
Residual uncertainty must remain transparent for every manual decision and must not be hidden.

## Why is operator decision kept visible?
Final acceptance is intentionally human and non-automatic; the report supports but does not replace that decision.

## Why generate both JSON and Markdown?
Markdown is operator-friendly for review, while JSON is machine-readable for consistent downstream validation and tooling.

## Why is the lab phase documented but not production-ready?
Documentation proves planning, guards, and read-only validation, but it does not replace real manual runtime evidence on hardware.

## Which seven runtime tests are still manually open?
Sudoers runtime dry-run, privileged runner validation dry-run, real write hardware E2E, failure injection hardware E2E, device reenumeration, hotplug/unmount race, and rollback runtime.

## Why is rootless E2E not enough?
Rootless E2E validates only the unprivileged path; privileged runtime, sudoers, and hardware-write risks remain unproven.

## Why is the privileged runner still blocked?
Until controlled manual runtime executions with complete evidence exist, the privileged path remains intentionally blocked.

## When can lab_ready_candidate become possible?
Only after all seven manual runtime executions pass in required order with complete and consistent evidence.

## Why use a next-phase gate?
The gate prevents unsafe follow-up steps and allows only clearly justified next phases under manual control.

## Why is manual runtime allowed while production stays blocked?
Lab validation may continue, but production remains blocked until privileged runtime evidence is complete.

## Why is lab_ready_candidate not a release approval?
`lab_ready_candidate` is a review state for human decision-making, not an automatic production switch.

## Why does automated deploy remain blocked?
Automation could bypass operator gates and safety stop conditions; this phase intentionally enforces manual control.

## Why are root backend and privileged daemon still forbidden?
Both models permanently increase attack surface and conflict with one-shot least-privilege design.

## Why run a precheck before manual runtime?
The precheck reduces unsafe starts by fail-closed validation of prerequisites, operator confirmations, and evidence planning.

## Why do dry-run runbooks need less hardware data?
Dry-run runbooks do not perform real writes, so some hardware checks are not applicable rather than hard-blocking.

## Why do write-related runbooks require hardware gate and guard?
These controls are the primary safety layer against wrong-target and media risks before any write-adjacent manual step.

## Why are operator confirmations mandatory?
Physical identification, backup state, and stop-condition awareness are not safely automatable and must be explicit.

## Why does precheck not start execution?
Precheck is strictly read-only and only provides readiness assessment, never a runtime execution trigger.

## Why create result files in advance?
Pre-created templates reduce omissions and provide consistent, later-validatable runtime evidence structures.

## Why only the allowed runtime-results path?
A fixed allowed root prevents path abuse, traversal, and unintended writes outside the evidence area.

## Why no automatic field population?
Runtime evidence must come from manual, traceable execution context, not from generated placeholder runtime values.

## Why must overwrite be explicitly confirmed?
This prevents accidental replacement of existing evidence; overwrite is only allowed with explicit intent.

## Why keep SHA256 fields even for dry-run?
A uniform schema simplifies validation and comparison; for dry-run those fields remain intentionally empty/null.

## Why use an edit checker before the validator?
The edit checker provides early human-readable guidance about gaps and risks before strict ingestion validation fail-closed blocks.

## Why does the checker not auto-correct?
Runtime evidence must remain manual and traceable; automatic corrections could distort observed runtime facts.

## Why are empty templates only review_required?
Empty values often mean "not filled yet". Before execution this is typically a review signal, not always an immediate safety blocker.

## Why do failed/mismatch states block?
`failed` or `verify_status=mismatch` are hard safety indicators and must not proceed as ingest-ready without explicit remediation.

## Why is suspicious target_device flagged?
System-like target patterns increase wrong-target risk and must remain visible even when later manually justified.

## Why use a bundle checker before the validator?
The bundle checker validates the complete seven-runbook set and sequence rules before ingestion evaluates the files as a whole.

## Why must all seven runbooks be present?
Lab acceptance depends on a fixed chain; missing steps leave safety gaps and prevent a credible end-to-end assessment.

## Why does ordering block submission?
Later steps assume earlier evidence; out-of-order files break the causal story of the runtime proof.

## Why does a failed runbook block later approval?
If an earlier step is not `pass`, later `pass` results violate the declared dependency chain and are fail-closed.

## Why does the bundle checker not modify files?
Evidence must remain manual and traceable; automatic edits would undermine runtime evidence integrity.

## Why is there a handoff gate after the bundle checker?
The bundle checker only assesses readiness; the handoff gate creates a separate auditable manifest and re-checks paths before validator intake.

## Why is there no automatic ingestion?
Ingestion remains an intentional manual or separately protected step; the gate does not replace operator judgment or validator execution.

## Why should the handoff manifest be immutable?
A stable manifest with explicit overwrite protection prevents silent redirection of validator inputs and improves traceability.

## Why are exactly seven runtime result files required?
The lab chain is defined for seven runbooks; fewer or more files would break acceptance logic and sequence assumptions.

## Why are paths checked again?
Files can disappear or paths can be tampered with between bundle check and handoff; the gate validates immediately before writing the manifest.

## Why run the validator in dry-run first?
Dry-run applies the same ingestion validation logic read-only and only writes a report so gaps surface before any real ingestion or approval step.

## Why is the handoff manifest not modified?
The manifest is the agreed handoff reference; changing it would break traceability between bundle check and validator execution.

## Why is there no automatic ingestion?
Ingestion remains a deliberately separate, manual or separately protected action; dry-run does not replace it.

## Why are paths checked again in dry-run?
Files can disappear or paths can change between manifest creation and validator execution; dry-run re-validates immediately before evaluation.

## Difference between handoff manifest and dry-run report?
The manifest lists the seven validator input files as the handoff artifact; the dry-run report captures validator output (including findings) and is stored separately under `handoff/`.

## Why create a seal?
A separate seal file provides a cryptographically checkable reference to the dry-run report without modifying the report itself.

## Why SHA256?
SHA256 is a standard, comparable fingerprint of the raw report bytes for integrity checks.

## Why treat reports as immutable?
Immutable sources are auditable; the seal pins that exact version, not a later edited file.

## Why must dry-run be ok first?
Only a successful dry-run yields a credible validator outcome; the seal must not canonize failed or ambiguous runs.

## Why index seal files?
A central index simplifies audits and overview without modifying individual seal files.

## Why index only validator_status ok?
Only seals marked consistently valid belong in the reference list; others are explicitly excluded.

## Why ignore invalid seals?
Bad artifacts would corrupt the index; they are reported but not ingested into the list.

## Why is the index read-only toward seals?
The index only aggregates metadata; seal and report integrity is preserved by not touching them.

## Why check seal consistency?
The index can drift or mis-reference; the audit compares entries to the filesystem and SHA256.

## Why recompute SHA256?
Only a fresh hash proves the current source report still matches the referenced bytes.

## Why are missing reports warnings?
Missing artifacts signal drift without necessarily invalidating every entry if at least one remains valid.

## Index vs. consistency audit?
The index lists expected seals; the audit verifies files, JSON, and hashes still match at runtime.

## Why generate a timeline?
It bundles key evidence files in time order with fingerprints for quick traceability.

## Why SHA256 per event?
Each entry pins the exact file contents at timeline generation time.

## Seal vs. timeline?
A seal attests one dry-run report; the timeline orders multiple artifacts (dry-run, seals, index, audit).

## Why is the timeline read-only?
Existing artifacts stay untouched; only a new aggregate file is produced.

## Why a final snapshot of the timeline?
It binds the timeline file with SHA256, fixing the evidence state without touching other files.

## What are timeline_sha256 vs snapshot_sha256?
`timeline_sha256` is over the raw timeline file bytes; `snapshot_sha256` signs snapshot metadata excluding itself.

## What does the final acceptance gate do?
It re-validates the final snapshot against the timeline file (SHA256) and only writes `validator_final_acceptance.json` with the outcome (`accepted` / `review_required` / `blocked`).

## When is acceptance `review_required`?
When the snapshot field `status` is `review_required` (for example because at least one timeline event was not `ok`).

## What does the final export package do?
It reads the full evidence chain from `handoff/`, validates all JSON files, and writes a final export package with SHA256 per included file.

## When is export blocked?
For `acceptance_status = blocked`, missing required files, symlinks, invalid JSON, or path-safety violations.

## Why is failure injection necessary?
It validates detection and blocking logic under real hardware conditions with controlled and reproducible fault cases.

## Why are productive drives forbidden?
Failure injection is restricted to test media to strictly protect real data and productive OS partitions.

## Simulation vs real hardware tests?
Simulation checks model logic; real hardware tests additionally cover reenumeration, mount changes, and permission boundaries.

## Why is `destructive=false` enforced?
All cases must stay reversible; destructive operations (for example mkfs/dd/wipefs) are excluded in this mode.

## Why preview only and no automatic execution?
Real hardware failure runs require human control; this module only produces planning and operator guidance.

## Why can real hardware tests be dangerous?
Wrong target media or unexpected reenumeration can cause data loss, so tests are restricted to dedicated test media and manual steps.

## Matrix vs execution preview?
The matrix defines fault scenarios; the execution preview turns them into concrete manual run steps and evidence expectations.

## Why is `destructive=false` still enforced in preview?
Preview mode must never trigger real damage and therefore remains strictly reversible and non-destructive.

## Why are operator checklists necessary?
They keep manual failure runs reproducible, safe, and auditable without automatic interventions.

## Why no automatic failure execution?
On real hardware, operators must control target media, sequencing, and stop conditions manually.

## Why are abort conditions important?
They prevent runs on wrong or productive targets and force an immediate stop when risk appears.

## Preview vs operator checklist?
Preview defines per-failure run planning; operator checklist provides concrete step-by-step controls including evidence requirements.

## Why are test sessions separate from checklists?
The checklist is the per-failure reference; the test session wraps the same rules into a runnable session plan with a session id and expected final state.

## Why is only `manual_only` allowed?
Hardware failure tests must not auto-start; the operator must initiate and stop each run explicitly.

## Why is `expected_final_state` important?
It defines which safe, demonstrable outcomes are acceptable after a manual run without touching productive media.

## Checklist vs test session?
The checklist is the controlled step list; the test session is the execution-oriented plan including session identity and final-state criteria.

## Why are test results stored separately?
Sessions describe the plan; the results file holds actual observations and evidence separately for auditability.

## Why document deviations?
Deviations from expected behavior matter as much as successful detection for risk and corrective decisions.

## Why is rollback_performed important?
It records whether a controlled teardown happened after a failure run without triggering automatic repair.

## Session vs result?
The session is the planned test unit; the result captures the actual run (time, operator, status, evidence, deviations).

## Why evaluate failure results?
To validate manual observations against preview detection rules and session constraints without touching hardware again.

## Why do mismatches matter?
They show when observed status diverges from expected and force review before treating the chain as clean.

## Result vs evaluation?
The result is the raw run record; evaluation is the read-only assessment with counters and findings.

## Why do deviations trigger review_required?
Any documented deviation implies extra risk or ambiguity and needs human follow-up.

## Why is a readiness gate needed?
It bundles all failure artifacts and safety checks before real hardware runs, without automatic execution.

## Why is destructive=false enforced globally?
So no case in the pipeline can be marked destructive and test-media rules stay explicit.

## Evaluation vs readiness?
Evaluation checks session results against preview rules; readiness additionally checks completeness and consistency across all pipeline files.

## Why do missing abort conditions block?
Without documented abort criteria, operators lack mandatory stop rules for unsafe runs.

## Why select laptop test runs?
After the readiness gate, a bounded, checked ordering of manual runs is fixed—without automatic execution or repair.

## Why is low risk ordered first?
Lower residual risk and operator load should precede medium risk when both are allowed.

## Why do productive markers block?
Any mention of productive or internal OS volumes in sessions or checklists stops selection to exclude data and system volumes.

## Readiness vs run selection?
Readiness checks completeness and global safety of pipeline artifacts; run selection filters and sorts individual manual sessions for the next laptop steps.

## Why is an operator runorder needed?
So selected runs can be executed in a fixed, repeatable order without automation and without mixing media/mount-risk contexts.

## Why are safer cases first?
Runs without media or mount changes and without rollback burden reduce context switches and residual risk before harder steps.

## Selection vs runorder?
Selection yields the allowed subset and a sort basis; runorder turns that into an explicit operator step list including grouping.

## Why is medium risk last?
Higher assessed risk should follow lower risk and a more stable setup so operators and environment are prepared.

## Why do we need an empty execution-log template?
So every manual run uses the same required fields and outcomes stay comparable, without automatic execution.

## Runorder vs execution log?
Runorder defines the step sequence; the execution log records the observed outcome for each step.

## Why do we need execution-log validation?
So only complete and consistent manual entries continue in the evidence chain.

## When is execution-log validation review_required?
When deviations are present, `observed_status` is `review_required`, or an abort was triggered.

## What is the laptop-failure test summary for?
It condenses validation into overall status, run counters, and findings for quick manual decision support.

## What is the laptop-failure final report for?
It provides the final manual status with recommendation (`proceed`, `review_before_next_run`, `blocked`) and binds the summary via SHA256.

## What is the final export package for?
It bundles final report, summary, validation, and execution log into one referencable package file with SHA256 per artifact.

## What is the laptop-failure evidence timeline for?
It orders all laptop-failure artifacts chronologically and adds SHA256 per entry for traceability.

## Difference between timeline, snapshot, acceptance, and export?
Timeline orders artifacts over time; snapshot freezes that timeline with hashes; acceptance evaluates the snapshot; export/finalized export bundles artifacts for traceable handoff.

## Why is there no automatic release?
The chain stays strictly read-only and manual, so no release is triggered without explicit human decision.

## Why are hashes rechecked before export?
To re-verify integrity and traceability of all relevant artifacts before the final package.

## Why is review_required not accepted?
`review_required` means manual review is still open and therefore cannot be treated as accepted completion.

## Why do STRICT phases increase version numbers?
Each completed STRICT phase must be traceable in history so evidence, tests, and implementation state map cleanly to a version.

## Difference between patch/minor/major?
Patch covers small fixes/docs, minor covers new STRICT modules and pipelines, major covers architecture or platform shifts.

## Why are internal test stages versioned?
`internal_testing` is still a binding milestone and should be reproducibly linked to version and artifacts.

## Why are there no automatic releases?
Version governance only tracks and validates consistency; releases are intentionally manual.

## Why is a centralized version source needed?
So frontend, backend, API, Tauri, and evidence all use the same project version without drift.

## Why are hardcoded versions risky?
They create conflicting states across UI, API, and artifacts and make diagnostics and acceptance harder.

## Difference between version governance and source of truth?
Governance defines when/how bumps happen; source of truth defines which file is canonical.

## Why does this not create automatic releases?
This flow only updates metadata and consistency checks, not tags, publish, or deploy actions.

## Why is pi-installer removed from active identifiers?
To consolidate runtime paths, services, env names, and app identifiers under Setuphelfer.

## Why are historical records kept?
Evidence, historical docs, and changelog entries are required for auditability and traceability.

## Legacy vs active runtime?
Legacy means documented/deprecated compatibility only; active runtime identifiers must not introduce new pi-installer names.

## Why are compatibility aliases needed?
They support controlled transition scenarios in read-only mode without hard runtime breaks.

## Why is there no blind replace?
Each path is classified; only `rename_now` under allowed project prefixes may be written automatically so evidence and history stay intact.

## Why do historical pi-installer records remain?
Evidence, changelog, and history paths are audit artifacts and are intentionally not overwritten.

## Why are legacy backups created?
Before each controlled rewrite the tool stores the original text under `handoff/legacy-backups/` so rollback is possible without Git.

## Why do old aliases still exist read-only?
Read-only compatibility avoids breaking environments that still set legacy env names, without introducing new legacy write paths.

## Why only 100 changes per cleanup cycle?
Small batches reduce risk, simplify review, and keep backups and diffs manageable.

## Why is cleanup done incrementally?
Each cycle is followed by a fresh inventory and consistency check so the state stays measurable and evidence/history stay protected.

## Why rescan after every cycle?
That is the only reliable way to count remaining active legacy identifiers and plan the next cycle.

## Why does the version stay at 1.7.0?
Identifier-only cleanup within the same phase does not require another SemVer bump.

## Why are hotspot analyses needed?
They group hits by impact area (backend, Tauri, env, scripts, packaging, tests) so cleanup can be planned deliberately instead of relying only on a raw count.

## Why are runtime identifiers more critical than comments?
Runtime identifiers affect paths, services, environment variables, APIs, and builds; comments are usually documentary and do not change live configuration.

## Why does an unknown identifier trigger `review_required`?
Without a known cluster it is unclear whether the hit is productive code, configuration, or documentation — manual triage is required.

## Why are tests cleaned up last?
Product code, startup scripts, and packaging affect real system behavior; test files follow once runtime paths are stable.

## Why is cleanup cycle 2 hotspot-driven?
So only paths prioritized by hotspot analysis are intersected with the safe rewrite plan — no repo-wide blind replace.

## Why does cycle 2 only clean critical/high items?
Medium and low hits are intentionally less urgent and are deferred to later passes or manual follow-up.

## Why are unknown clusters not auto-edited?
Without a clear cluster assignment the risk is not controllable; unknown stays for manual triage.

## Why at most 50 changes per hotspot cycle?
The cap keeps diffs, backups, and review load manageable and reduces error risk on productive paths.

## Cleanup cycle vs runtime elimination?
Cycles 1/2 are bounded batches; **runtime elimination** builds explicit targets from hotspot/consistency, intersects the safe plan, and only writes clearly allowed productive paths.

## Why remove runtime identifiers first?
They affect env vars, install paths, units, and app IDs — that is live operational risk, not comment/doc lines.

## Why do legacy aliases stay read-only?
So legacy names remain documented and compatible without introducing new pi-installer write paths.

## When is a patch bump to 1.7.1 allowed?
Only when the elimination postcheck reports no active runtime identifiers, critical/high in hotspot analysis are zero, and identifier consistency is not **blocked** — then **1.7.1** is prepared as a recommendation without automatically editing version files.

## Why is zero state required before 1.7.1?
Zero-state verification bundles inventory, hotspot, consistency, and the alias contract — without a green result a version jump would be unproven.

## Why is the patch bump not automatic?
`no_auto_apply` and the explicit apply flag keep SemVer and evidence under deliberate human approval.

## Why may alias remnants be allowed?
Read-only compatibility in `compatibility_aliases.json` and history is intentional when no productive hits remain.

## Why do runtime remnants block?
Any remaining PI_INSTALLER/path/service/app identifier outside allowed contexts contradicts “elimination complete”.

## Why is `pi-installer` forbidden in runtime from now on?
The branding guard prevents old product names from reappearing in code, config, env, or packaging — Setuphelfer is the only supported runtime brand.

## Why keep historical evidence?
Evidence, history, migration paths, and `compatibility_aliases.json` may show legacy strings without failing the guard.

## Why does the guard not modify files?
Checks plus evidence JSON only — no rewrite, so no silent text edits outside review.

## Why is Setuphelfer the only runtime brand now?
A single brand and path space reduces support errors, double installs, and wrong systemd/app IDs.

## What happens to old pi-installer installations?
The legacy runtime compatibility pipeline only evaluates handoff/evidence data and produces inventory, coexistence analysis, and recommendations — no real migration on the target system.

## Why are old configs not deleted?
Deletes are irreversible and bypass review; archiving, read-only, and disable are recommended instead.

## Why can coexistence be problematic?
Duplicate services, desktop entries, or parallel paths can fight over ports, env, and backups — analysis flags those conflicts.

## Why recommend disable instead of delete?
`systemctl disable` (manual, after approval) keeps rollback/data options; delete is often too risky for legacy installs.

## What is the laptop live probe handoff?
A three-step flow (plan, read-only execute, final gate) that only performs HTTP read operations against the backend — no restore, no real verify paths without an explicit flag.

## Why does execute require an explicit flag?
So live requests are never accidental; `explicit_execute_live_probe=true` is the deliberate opt-in.

## Why do legacy strings in API responses block?
If pi-installer / `PI_INSTALLER_` strings appear in JSON responses, that conflicts with the Setuphelfer branding goal — the final gate stays blocked.

## Why Debian Live for the rescue stick baseline?
Stable packages, broad hardware support, a good fit for the Python/apt Setuphelfer stack, and maintainable operations — see `docs/rescue/SETUPHELFER_RESCUE_STICK_ARCHITECTURE_EN.md` and the `rescue_live_os_base_decision.json` handoff.

## Why is USB not written yet?
This phase only produces architecture, gates, and build preparation; USB flashing (`dd`) stays behind a later, explicit gate and the build safety policy (`docs/developer/RESCUE_STICK_BUILD_SAFETY_POLICY.md`).

## Why is restore from the stick preview-only for now?
Automatic restore is destructive and needs its own sessions, tokens, and hardware gates — the MVP strand allows analysis, verify, and preview only.

## Why is Raspberry Pi tested later?
amd64 UEFI laptops are the first controlled path; ARM/RPi needs separate images, firmware, and matrix entries under `later`.

## Why is Secure Boot `review_required` initially?
Shim/signing, firmware behaviour, and lab hardware are not part of an automatic OK gate yet — the evaluation is explicit in the live-OS decision and ISO test matrix (`later`).

## Why VM-only for the rescue ISO test first?
Controlled environment, snapshots, no production host-disk risk, and simple NAT access — see `docs/developer/RESCUE_VM_TEST_SAFETY_POLICY.md`.

## Why does the runtime probe stay read-only?
Restore execute and real write paths stay blocked; HTTP checks (version, health, inspect, branding) are enough for phase-1 acceptance.

## Why still no real USB stick?
`dd` / USB flashing stays outside the gates; the ISO stays under `build/rescue/output/`.

## Why no automatic restore?
Restore remains deliberately manual/session-bound; the ISO strand validates reachability and safety only.

## Why Debian Live for the build?
Stable baseline, `live-build` tooling, and alignment with the existing Setuphelfer stack — see `docs/deploy/DEPLOY_RESCUE_ISO_BUILD_AND_VM_VALIDATION_EN.md`.

## Why read-only mounts in rescue live?
Any write to internal system disks is destructive and hard to undo; read-only mounts allow inspection (EFI, root, backups) without changing data — see `docs/deploy/DEPLOY_RESCUE_LIVE_RUNTIME_AND_STORAGE_VALIDATION_EN.md`.

## Why no automatic EFI repair?
Firmware, NVRAM, and bootloaders are fragile; automatic repair could brick systems. This phase is analysis and gates only.

## Why no restore directly from the stick?
Restore is session/token-bound and needs explicit targets; the stick strand stays at discovery, preview, and safety.

## Why external evidence targets are recommended?
RAM live logs are lost on reboot; export to USB or an explicitly chosen non-system target preserves evidence without implicitly overwriting system data.

## Why SSH is not enabled automatically?
Remote access widens the attack surface; remote help stays plan-only until an operator deliberately starts SSH — see remote-help handoff and safety gate.

## Why restore preview only?
Real restore writes are irreversible and need separate execute gates; the simulation phase only lists affected paths, mounts, and risks — see `docs/deploy/DEPLOY_RESCUE_RECOVERY_SIMULATION_AND_HARDWARE_VALIDATION_EN.md`.

## Why read-only recovery?
Internal system disks must not be written in this phase; target validation, mounts, and preview stay analysis-only.

## Why hardware tests matter?
VMs and synthetic handoffs do not cover firmware, NVMe, Wi‑Fi, and real USB mounts; the hardware test chain documents the expected flow on reference machines.

## Why backup verify is mandatory?
Without a manifest/SHA256 chain, restore preview would be unsafe; verify detects damaged or inconsistent archives before any later write phase.

## Why is a real ISO not built yet?
The readiness pipeline only produces JSON handoffs, scans, and gates; a real image stays behind a separate, explicitly approved build step — see `docs/deploy/DEPLOY_RESCUE_ISO_READINESS_PIPELINE_EN.md`.

## Why Debian Live?
Stable package baseline, `live-build` tooling, and alignment with the existing Setuphelfer stack.

## Why read-only recovery first?
Writes to system disks are risky; preview and verify strands run before any later execute phase.

## Why no automatic restore?
Restore is destructive and needs sessions, tokens, and target checks — no silent automation in the ISO readiness pipeline.

