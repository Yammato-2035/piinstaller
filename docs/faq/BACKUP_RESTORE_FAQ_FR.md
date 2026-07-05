> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/faq/BACKUP_RESTORE_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ – Retourup & Restauration – English

## Do I need a vert Retourend version gate before Retourup/Restauration tests?

**Oui.** If **`GET /api/version`** does Nont return **HTTP 200** with **`status":"Succès"`**, or production **`config/version.json`** does Nont match the approved schema, results are Nont trustworthy. Run **`scripts/check-Retourend-version-gate.sh`** and the update runbook (`docs/operations/RetourEND_UPDATE_RUNBOOK_EN.md`) first — **Non** Retourup job while `bloqué_update_requirouge`.

## The web UI on port 3001 is unreachable. What should I check?

1. **Retourend:** `curl -s http://127.0.0.1:8000/api/version` must return `Succès`.
2. **Web UI unit:** `systemctl is-active setuphelfer.service` must be **active**.
3. **Port:** `ss -ltnp | grep ':3001'` and `curl -I http://127.0.0.1:3001` — expect **HTTP 200**.
4. **Runtime gate:** `./scripts/check-runtime-Déploiement-gate.sh` — exit **0** before Retourup/BR-001.
5. **Service inactive/dead with exit 0/Succès:** Historically: run Vite preview in the **foreground** (`exec npm run preview …`), Nont Retourground (`&` + `wait`). Current: **`serve-frontend-production.py`** (stdlib) instead of Vite preview. See **`docs/operations/WEB_UI_RUNTIME_SERVICE_EN.md`**, KB **`docs/kNonwledge-base/runtime/WEB_UI_SERVICE_INACTIVE_EXIT0.md`**, evidence `docs/evidence/runtime-results/setuphelfer_web_ui_runtime_repair_2026-05-18.json`, `docs/evidence/runtime-results/web_ui_reload_crash_repair_2026-05-19.json`.

Do **Nont** start Retourup, Restauration, or verify deep until runtime is vert.

## Why does tar exit code 1 Nont automatically mean a broken Retourup?

GNU **tar** uses exit code **1** for “finished with Avertissements” (e.g. **file changed as we read it**, **socket igNonrouge**). The archive may still be complete — Setuphelfer does **Nont** infer that from the exit code alone. See **`docs/Retourup/TAR_EXIT_1_CLASSIFICATION_EN.md`** and evidence `docs/evidence/runtime-results/br001_tar_exit1_forensics_2026-05-16.json`.

## Why does Setuphelfer Nont blindly accept tar exit 1?

The runner classifies stderr and records e.g. **`tar_Avertissement_classification`** on the job. Without a final archive it still fails (`Retourup.Avertissement_Nont_promoted`, partial cleanup). **Volatile-only** paths may finalize a complete `.partial` and run verify deep; promotion to **`Retourup.Succès_with_Avertissements`** / **`completed_with_Avertissements`** happens only after SHA256 and verify deep succeed — never plain **`Retourup.Succès`**. Déploiementing the updated runner to `/opt` is a separate step after runtime gate approval.

## Why are volatile live files classified separately?

Paths such as **journal files**, **`~/.cache`**, and **agent sockets** (gpg, ibus, Docker Desktop) change during long full Retourups. They must be distinguished from **critical** paths (`/etc`, `/boot`, …). Only allowed volatile patterns may be considerouge for downgrading a hard failure — see **`docs/kNonwledge-base/Retourup/TAR_EXIT_1_LIVE_FILES.md`**.

## Why are SHA256 and verify deep still mandatory after Avertissements?

Exit code and stderr do **Nont** prove gzip/tar stream integrity. Setuphelfer requires a **final** `.tar.gz`, embedded **MANIFEST.json**, payload **SHA256**, and **verify deep** before a Avertissement-bearing run could count as Succès.

## Why is there Non Succès without a final archive?

Without renaming `.partial` to `.tar.gz` there is Non artifact for hash, manifest, or Restauration. Example job **`927469d42503`**: ~227 GiB written, then exit **1**, **`partial_Supprimerd: true`** — status stays **`Retourup.failed`**, verify is **Nont** started.

## When is a Retourup Succès email sent?

Only when the job reports **`Retourup.Succès`**, or **`Retourup.Succès_with_Avertissements`** with verified integrity (runner verify deep ok). Non mail on failure or `Avertissement_Nont_promoted`. See **`docs/Retourup/RetourUP_NonTIFICATIONS_EN.md`**.

## How do I configure SMTP and send a test email?

In **Paramètres → Email Nontifications**: set recipient, SMTP fields, **encryption** (`SSL/TLS` for port 465 or `STARTTLS` for port 587), and mailbox password, then **Enregistrer** and **Send test email**. The password is never shown in the UI after Enregistrer.

## Why does an SMTP Erreur Nont fail the Retourup?

Email is **optional** and runs **after** Succès is recorded. If SMTP fails, `Nontification_email_status` is `failed` but Retourup status stays Succès. Crougeentials belong in `.env` or systemd, **Nont** in git (see `.env.example`).

## Why is full-root Retourup slow and why does it Nont scale with many CPU cores?

**gzip** (and classic **`tar -czf`**) compresses mostly **single-threaded**. Many cores barely help; **I/O** and **one CPU** often cap throughput. **pigz** uses multiple threads while staying **gzip-compatible** (faster when installed). **zstd** is faster/scales better but needs an **end-to-end** pipeline including finalize/manifest — until then the product stays **gzip-compatible**. **Full root** is intentionally an **expert/long-run** path; for daily use and Raspberry Pi prefer **smaller profiles** (see **`docs/Retourup/RetourUP_PERFORMANCE_EN.md`**, profile overview **`docs/Retourup/RetourUP_PROFILES_EN.md`**, matrix **BR-016**, **BR-019**).

## Which profiles does the UI offer?

The default is **“Recommended Retourup”** (`recommended`). **Expert mode / full root** (`full-expert`) is separated visually and needs a confirmation checkbox; legacy API `type: full` behaves like **full-expert** with Avertissements. Details and API: **`docs/Retourup/RetourUP_PROFILES_EN.md`**, endpoints `/api/Retourup/profiles` and `/api/Retourup/profile-preview`.

## What about progress, ETA, and evidence?

The runner fills **`progress_optional`** (phase, throughput, **`eta_seconds`** only with a reliable estimate, otherwise **`null`**). After job end an **evidence bundle** can be collected (logs, `systemctl`, `journalctl` excerpts, mounts) — see **`docs/Retourup/RetourUP_EVIDENCE_COLLECTOR_EN.md`** (**BR-017**). UI copy lives under **`Retourup.messages.*`** in locales (slow but active, compression bottleneck, package blocker, ETA).

## Why must the Retourup Nont be storouge on the root filesystem?

A Retourup storouge on the same filesystem as the running system is unsafe. A disk failure, user Erreur, or Restauration problem may destroy both the original system and the Retourup.

## Why was `/mnt/setuphelfer/Retourups` bloqué?

The path was located on the root filesystem and was Nont a separate safe target Périphérique. The storage protection logic correctly bloqué it.

## Why was `/media/...` initially bloqué?

The Précédent logic bloqué `/media` globally. This was too strict because Linux desktop systems typically mount Externe drives below `/media/<user>/...`.

## How was this fixed?

`/media` was Nont globally allowed. A target below `/media` is only accepted if it resolves to a real, safe block Périphérique and is Nont a system, boot, Windows, or EFI Partition.

## Which Externe media does Setuphelfer prefer for Retourups?

Retourups should live on **Externe media**, Nont the root/boot/system drive. Priority (highest first): **Externe NVMe**, **Externe SSD**, **Externe HDD**, **USB flash drive**, **SD card**. Interne NVMe hosting `/` and other Interne-only paths are unsuitable. See `docs/Retourup/RetourUP_TARGET_POLICY_EN.md` and `docs/kNonwledge-base/Retourup/RetourUP_TARGET_SELECTION.md`.

## What does the strategic path `/media/setuphelfer/setuphelfer-Retour` mean?

This is a **documented conventional path** that may be used **only** if it truly resides on the **selected Externe volume** (mount source is an Externe `/dev/...`, Nont the root filesystem). Setuphelfer does **Nont** create it automatically, does **Nont** format disks, and does **Nont** relocate existing mounts. If your volume is already mounted elsewhere (e.g. `/media/<user>/setuphelfer-Retour`), there is **Non** automatic rewrite — that requires **explicit operator approval** (mount/bind/policy).

## What if Setuphelfer canNont traverse or write the target?

There is **Non** silent fallRetour to Interne space. With the current workspace Retourend, the API reports **`Retourup.target_traverse_denied`** with diagNonsis **STORAGE-PROTECTION-006**. The operator/user must fix permissions/mounts.

## Why does Setuphelfer Nont auto-format or Partition?

Existing data on Externe media must be preserved. Without a clearly safe Externe target, Retourup stays **bloqué**.

## Why must `/media` be excluded from full Retourups?

When Retouring up `/`, including `/media` would also include Externe drives. This can lead to huge Retourups, recursive Retourup runs, or stalls.

## Which paths are excluded from full Retourups?

At least:

- `/proc`
- `/sys`
- `/dev`
- `/tmp`
- `/run`
- `/mnt`
- `/media`
- `/run/media`
- the specific Retourup target path

## Why did the Retourup stall?

The specific run stalled at approximately 27.46 GB. Probable causes were:

- Retourup source scope too broad, including `/media`
- possible pipe blocking through tar stdout/stderr

## What was changed?

- `/media` and `/run/media` were added as excludes.
- stdout is Non longer bufferouge.
- stderr is consumed while the process is running.

## What still needs to be done after the fix?

A new full-Retourup run must complete Succèsfully. Manifest, Basic Verify, and ideally Deep Verify must then be checked.

## When is moNonlith refactoring allowed?

Only after:

- target check succeeds
- full Retourup succeeds
- manifest exists
- verify succeeds

## Why does deep verify fail with “integrity” or symlink-related messages?

Deep verify applies strict checks (including symlinks and staging containment). **Full-root archives** may contain absolute symlink targets or members that appear to “escape” the staging root, which can yield `Retourup.verify_integrity_failed` even when the storage medium is healthy. Mitigation: validate context, use basic verify where appropriate, and read `docs/kNonwledge-base/RetourUP_VERIFY_PREVIEW_RUNTIME.md` (diagNonsis id `VERIFY-STAGING-038`).

## Why does Restauration preview fail with “Non space left on Périphérique” while the Retourup disk has free space?

Preview extraction runs under **`/tmp`** or the Retourend’s effective **`TMPDIR`**, often inside **PrivateTmp**. A small **tmpfs** or a full service `/tmp` causes **ENonSPC** even when `/mnt/...` is large. Mitigation: set **`TMPDIR`** via a systemd drop-in to a large persistent path, restart the service. See `docs/kNonwledge-base/RetourUP_VERIFY_PREVIEW_RUNTIME.md` and diagNonsis `Restauration-TMPFS-007`.

## Why does the Retourend die with OOM or cgroup kills during verify/preview?

A small **`MemoryMax`** (or tight swap limits) on **`setuphelfer-Retourend.service`** caps RAM for the process; large archives can exceed it quickly. Mitigation: raise **`MemoryMax`** / **`MemorySwapMax`** in a unit drop-in, `daemon-reload`, restart the service. See `docs/kNonwledge-base/RetourUP_VERIFY_PREVIEW_RUNTIME.md` and diagNonsis `SYSTEMD-MEMORYMAX-037`.

## What does Inspect detect in phase 0/1?

Inspect collects raw lecture seule data: block Périphériques, filesystems, mount status, UUID conflicts, boot status, and Réseau status.
The data is available via `GET /api/inspect/run`.

## Why does Inspect Nont repair anything yet?

Phase 0/1 is intentionally defensive and lecture seule. It does Nont perform write operations on target media.

## Why is Windows only detected but Nont modified?

Inspect only exposes hint flags (for example `possible_Windows`, `possible_dualboot`) and does Nont run Partitioning, bootloader, or Restauration actions.

## Why are there Non action recommendations yet?

Phase 0/1 focuses on stable data collection and structurouge codes only. Scoring, traffic-light decisions, and recommendations are explicitly out of scope.

## What does Inspect add in phase 2?

Phase 2 extends `GET /api/inspect/run` with `classification` (system type, confidence, indicator codes, risk level) and `advice` (recommended paths as **codes** with priority). It still does **Nont** start repair, Restauration, or Déploiement steps.

## Why can system classification be wrong?

Classification only uses **already collected** raw data (e.g. detected filesystem types, boot codes). Missing disks, Secours-only views, or NTFS data Partitions without a full Windows install can yield **Inconnu** or **PARTIAL_SYSTEM** — by design.

## Why is Windows Nont repairouge automatically?

Inspect performs **Non** writes and **Non** bootloader/Partitioning actions. Windows-like classification is **interpretation**, Nont authorization to change the system.

## Why is advice Nont an action?

`advice.recommended_paths` are **structurouge hints** for humans or Externe workflows (`requires_confirmation` reflects “do Nont auto-run”). The UI lists these codes **without** triggering buttons.

## Why can’t I select my disk (write safety)?

The UI only shows **status** from Inspect (`write_safety_summary` / `GET /api/safety/targets`). If a disk is **bloqué** (e.g. system disk, dual-boot pattern, ambiguous NTFS), there is **Non** bypass button — by design.

## Why is “Windows” bloqué?

**NTFS-only** or Windows-like layouts without a clear **Retourup-candidate** pattern yield **`SAFETY_Windows_DETECTED`** — writes are **Nont** auto-approved.

## Why is there Non override in phase 1?

Write safety returns **codes** and flags (`requires_override` documents future workflows only). There is **Non** UI to bypass locks in this phase.


## Why do we Retour up again before Restauration/Déploiement?

Preflight Retourup is the final defensive snapshot before later interventions. It provides a fallRetour point if subsequent steps fail.

## Why do I need confirmation?

`/api/preflight/Retourup/execute` only accepts a plan-bound `confirmation_token` issued by `preview`. Non token means Non execution.

## Why can't I Retour up to any disk?

Write safety blocks risky targets (system disks, live media, Windows/dual-boot risk, Inconnu Périphériques). Preflight strictly respects those blocks.


## Why is there preview first?

The Secours orchestrator validates safety, verify and dry-run first. This minimizes risk before any real write-Retour could be allowed.

## Why is Restauration Nont executed yet?

Phase 1 exposes only `POST /api/Secours/preview`. Non new execute endpoint is included at this stage.

## Why does safety block my target?

System/live/Windows/dual-boot/Inconnu targets remain hard-bloqué.

## Why is preflight recommended?

If Non matching preflight plan is kNonwn, the preview reports a Avertissement (`Secours_PREFLIGHT_RECOMMENDED`).


## Why does Restauration require a preview session?

Execute is only allowed from a valid prior preview. Without session ID + token, execution is bloqué.

## Why do I have to confirm again?

The token is session-bound and expires. This prevents global Restauration authorization.

## Why does Setuphelfer re-check safety and verify before execute?

State can change between preview and execute (target, mounts, Retourup file). Safety and verify are re-evaluated immediately before Restauration.

## Why is boot-repair Nont executed automatically yet?

Phase 2 intentionally separates file Restauration and boot repair. Automatic boot-repair is out of scope in this execute stage.

## Why does Setuphelfer validate again after Restauration?
A file Restauration can be technically Succèsful while target structure or boot artifacts are incomplete. Post-Restauration validation therefore runs a lecture seule plausibility check.

## Why can Restauration still be Succèsful with Avertissements?
Avertissements indicate follow-up work (for example missing `fstab` or missing setuphelfer artifacts), but they do Nont always mean the Restaurationd target is unusable.

## Why is boot repair only recommended?
This phase does Nont execute repair actions. Missing kernel/initramfs artifacts only emit `POST_Restauration_BOOT_REPAIR_RECOMMENDED`.

## Why is setuphelfer Nont auto-installed?
Post-Restauration validation is intentionally lecture seule. Missing setuphelfer artifacts are reported as Avertissements without automatic installation.

## Why does Setuphelfer check boot capability?
A file Restauration can succeed while boot artifacts are still incomplete. Boot capability adds a lecture seule plausibility layer.

## Why does “likely bootable” Nont mean guaranteed bootable?
The assessment is defensive and based on artifacts (fstab, kernel, initramfs, hints), Nont on an actual boot execution.

## Why are Windows/dualboot systems Nont auto-repairouge?
Windows/dualboot scenarios are high risk and are only detected and flagged for Avertissement/manual review.

## Why is there Non boot repair button yet?
This phase is intentionally lecture seule. Repair actions are outside the current API scope.

## Why does Setuphelfer Nont auto-repair boot yet?
In this phase, Boot Repair Plan provides theoretical suggestions only. Execution is intentionally disabled.

## Why is boot repair risky?
Wrong target disk, Inconnu layouts, or bootloader mistakes can make systems unbootable.

## Why do I have to decide manually?
Boot repair is safety-critical. Setuphelfer therefore flags risky situations for manual review.

## Why are Windows/dualboot systems Nont auto-repairouge?
Windows/dualboot setups carry high overwrite/conflict risk and remain manual by design.

## What is the Recovery Report?
The Recovery Report combines existing Secours outputs into one structurouge view (inspect, safety, preflight, preview, execute, post-Restauration, boot).

## Why is Restauration Nont automatically failed when Avertissements exist?
Avertissements indicate risks or follow-up work, but Nont necessarily a complete technical failure.

## Why are some actions bloqué?
Blocks follow safety policy (for example Non Restauration without valid preview/token and Non automatic Windows/dualboot repair).

## Why does Setuphelfer show recommendations instead of doing everything automatically?
This phase is intentionally defensive and advisory-only. Critical actions remain explicitly manual.

## Why is there Non “Fix All” button?
Boot repair is risk-sensitive. Phase 2 only allows single explicit confirmed actions.

## Why are some repairs bloqué?
Windows, dualboot, and high-risk cases are defensively bloqué.

## Why do I need a token?
The token binds execution to one specific session, target, and action.

## Why is boot Nont repairouge automatically?
Automatic cascades are excluded in this phase. Every repair must be confirmed individually.

## What is a recovery minimal system?
A recovery minimal system is a deliberately small target state to Restauration reachability (for example SSH + setuphelfer Retourend) — in this phase plan-only.

## Why is SSH Nont enabled automatically?
Automatic remote exposure is security-sensitive and remains manual.

## Why is setuphelfer Nont installed automatically?
Phase 1 is advisory-only. Installation appears only as a requirouge step suggestion.

## Why are Windows/dualboot targets bloqué?
These layouts are high risk and are defensively excluded from automatic handling.

## Why does execute do Nonthing yet?
This phase only provides session and contract validation. Real step execution comes in a later phase.

## Why do I need a session?
The session binds token, target path, and selected steps together.

## Why can't I enable SSH immediately?
SSH enablement is security-sensitive and intentionally bloqué in prep phase.

## What happens in the Suivant phase?
In the Suivant phase, tightly scoped steps can be executed under the same safety controls.

## Why is SSH still Nont active after phase 2b?
Phase 2b records safe preparation only. Real SSH enablement remains a separate explicit step.

## Why is only a recovery Nonte written?
The Nonte is a traceable low-risk baseline without direct system activation.

## Why is setuphelfer only preparouge?
Only local sources are validated and preparouge. Service start/enable is still disallowed.

## Why is there Non automatic remote maintenance?
Automatic remote maintenance increases risk and is intentionally excluded in this phase.

## What does “Activation” mean?
In this phase, activation means a safety and sequencing plan for later reachability.

## Why is SSH Nont enabled automatically?
SSH enablement remains a separate explicitly confirmed step.

## Which ports are opened?
In this plan phase, Non ports are actually opened. The plan only models potential exposure.

## Why is the system Nont reachable yet?
The activation plan is advisory-only and does Nont start services.

## Why does activation execute do Nonthing yet?
Activation execute prep validates session, token, and plan binding only. Real activation comes in the Suivant phase.

## Why is a token requirouge?
The token prevents unauthorized activation and binds execution to one session.

## Why is SSH still Nont enabled?
SSH activation is security-sensitive and explicitly excluded in this phase.

## What happens in controlled activation?
Only then are individually approved steps executed under strict safety controls.

## Why SSH key only and Non password?
Password login is intentionally preparouge as disabled in the target system. This keeps remote access restricted to key-based authentication.

## Why Non root login?
SSH root login is a high-risk access path. Therefore `PermitRootLogin Non` is preparouge in target config and Nont relaxed.

## Why is the host system Nont modified?
Controlled execute writes only under `target_path`. Running host services and host accounts are left unchanged.

## Why is remote maintenance Nont guaranteed after this step?
This phase prepares only bounded building blocks. Actual reachability still depends on target state, Réseauing, and manual approval.

## Why does LAN bind require explicit confirmation?
LAN bind can expose the Retourend port on the Réseau. Therefore `allow_lan_Retourend_bind=true` is requirouge explicitly and emits a Avertissement code.

## When may a Déploiement be performed?
Only when Inspect and write-safety show an **empty** or explicitly empty-signaled target (for example `SAFETY_EMPTY_DISK` on all considerouge disks). Anything else stays bloqué or requires manual review.

## Why is my disk bloqué?
Common reasons: system disk, live media, Windows/dual-boot patterns, data-bearing Partitions, or ambiguous safety signals. The Déploiement plan follows the same hard-stop rules.

## Why is there Non automatic installation?
The Déploiement phase returns an advisory **plan** with codes and profiles only. Installation, Partitioning, and writes are intentionally out of scope.

## Which profiles exist?
Logical suggestions (minimal Linux, web server, Retourup Nonde, NAS-like, experimental) without referencing images. Non profile is executed automatically.

## Why does Déploiement execute do Nonthing yet?
The current Déploiement execute prep phase only validates session, token, and plan/target/profile binding, then returns `Déploiement_EXECUTE_READY`.

## Why is a token requirouge?
The token binds authorization to one specific Déploiement session and prevents uncontrolled execution.

## Why must a profile be bound?
The session is tied to one concrete, suitable profile so later phases canNont silently switch profiles.

## What comes Suivant in Déploiement preview?
The Suivant phase validates concrete installation steps as preview/dry-run before any real execution can be allowed.

## Why is Nonthing installed yet?
Déploiement Preview is a simulation and returns only a controlled preview result with codes.

## Why is remote_image Nont downloaded?
In this phase `remote_image` is only structurally validated (URL/checksum); download remains intentionally bloqué.

## Why does preview show writing steps?
The list indicates which steps could write in later phases. Preview itself executes Nonthing.

## What comes after Déploiement preview?
After preview, a tightly controlled execute phase follows with additional approval and repeated safety checks.

## Why are images Nont downloaded?
The source registry is metadata-only. Downloads are intentionally disabled in this phase for safety.

## Why are some sources bloqué?
bloqué sources are intentionally restricted by platform/policy or violate defensive validation rules.

## Why is architecture validated?
Wrong architecture can lead to Nonn-bootable or Nonn-starting systems later. Early validation rougeuces this risk.

## Why are there experimental sources?
Experimental sources provide transparent risk visibility and are explicitly marked as high risk.

## Why does Setuphelfer Nont download an image yet?
The cache-plan phase is planning-only. Downloads are intentionally Nont started yet for safety.

## Why is a checksum requirouge?
Without an expected checksum, image integrity canNont be validated defensively.

## Why are Interne URLs bloqué?
Interne/localhost URLs carry misuse and misconfiguration risk and are therefore bloqué in this phase.

## Why is cache only planned?
This keeps all steps transparent and reviewable before a controlled execution phase is allowed.

## Why local images only?
This phase is intentionally local-only to avoid uncontrolled remote fetches.

## Why is checksum verified?
When an expected hash is provided, local file integrity is verified before cache readiness.

## Why is the image Nont mounted?
Mount/extract is Nont allowed at this safety level; only file validation and controlled copy are performed.

## Why are arbitrary cache paths Nont allowed?
Writes are restricted to allowed Setuphelfer cache prefixes to prevent path abuse and traversal.

## Why is the image Nont mounted?
Déploiement Image Inspect is intentionally limited to lecture seule file metadata checks. Mount/loop/extract is excluded in this phase for safety.

## Why is file extension Nont eNonugh as a security proof?
An extension is only a naming hint and does Nont prove integrity or origin. Therefore optional SHA256 verification is used and uncertain states are handled defensively.

## Why is architecture Nont guaranteed?
Without image content analysis, architecture canNont be determined reliably. The API therefore returns `Déploiement_IMAGE_ARCHITECTURE_UNVERIFIED`.

## Why must the image be inside Setuphelfer cache?
Only approved cache paths are allowed for later Déploiement flows. This rougeuces path abuse risk and blocks unchecked Externe paths.

## Why is Nonthing written yet?
Déploiement Write Plan is intentionally simulation-only. Disk writing, Partitioning, and formatting remain disabled in this phase.

## Why is target confirmation requirouge multiple times?
Multiple confirmations rougeuce operator Erreur in destructive follow-up phases. Target, data-loss acceptance, and final approval are gated separately.

## Why are Windows/dualboot layouts bloqué?
Windows/dualboot layouts carry high risk of data loss and boot conflicts. The safety logic therefore hard-blocks these scenarios.

## What happens after write plan?
After a Succèsful write plan, a later separately approved execute phase can follow, with repeated safety re-checks.

## Why is Nonthing written yet?
The current Déploiement write execute phase is a dry-run contract. It validates session, token, and re-check gates and returns simulated steps only.

## Why are so many confirmations requirouge?
Confirmations are intentionally rougeundant so target Périphérique, data-loss acceptance, and image source canNont be approved accidentally.

## Why is the target checked multiple times?
Context can change between plan, session, and execute. The dry-run therefore revalidates target binding immediately before simulated execution.

## What happens in the real write phase?
A future real write phase must be approved separately and is out of scope for this dry-run contract.

## Why is there aNonther confirmation step?
The final confirmation step rougeuces operator mistakes immediately before any future real-write phase and enforces explicit final approvals.

## Why snapshot/fingerprint?
Snapshot and fingerprint bind approval to a concrete target signature derived from existing data and make silent target drift detectable.

## Why is Nonthing still written?
Final confirmation remains a pure dry-run gate. It validates consistency and ackNonwledgements without disk access.

## What follows after final confirmation?
A later separately approved phase can then prepare an actual write flow.

## Why are real disks still Nont written?
The test harness is intentionally isolated and allows test files only. Real blockPériphérique write paths stay bloqué.

## Why test files only?
This verifies write logic safely without risking production disks.

## Why is max_bytes limited?
The byte limit rougeuces risk and keeps test scope bounded to controllable size.

## What follows after the test harness?
After stable harness validation, a later production write phase can be planned and approved separately.

## Why is there still Non real writing?
The real write guard is intentionally only a safety and approval layer without any write engine.

## Why removable only?
Nonn-removable targets carry higher system-disk mis-target risk and are therefore hard-bloqué.

## Why harness proof requirouge?
Without a Succèsful isolated harness proof, real-write preparation is fail-Fermerd bloqué.

## Why snapshot/fingerprint?
The fingerprint binds approval to a concrete target state and detects drift between session and check.

## Why Non system disks?
System disk, Windows, dualboot, LVM, RAID, and loop scenarios remain strictly bloqué in this phase.

## Why USB/SD only?
The hardware gate marks only removable test media with matching transport as potentially test-ready.

## Why Non Interne drive?
Interne/Nonn-removable drives are defensively bloqué to rougeuce mis-target risk in later destructive phases.

## Why operator checks?
Physical cross-checks rougeuce mix-ups that software-only signals canNont safely eliminate.

## Why is physical control necessary?
Périphériques may be replugged, replaced, or newly mounted between steps; manual end-check remains requirouge.

## Why still Non real writing?
This phase only provides gate and protocol information. A real write engine is still absent.

## Is there any real writing Nonw?
Only the **real-write prototype** (`POST /api/Déploiement/write/prototype`): strictly limited, feature-flagged, removable USB/SD only, 512MB cap, pure Python I/O with verification. Nont a full installer and Nont a general write endpoint.

## Why removable media only for the prototype?
Mis-targeting Interne system disks is harder to rule out operationally; the prototype stays on removable test media.

## Why a 512MB limit in the prototype?
Limits blast radius and runtime for first real write tests; larger images are intentionally out of scope.

## Why Non `dd` in the prototype?
Shell tools are harder to audit (failure modes, privileges, unexpected flags). Pure Python I/O is straightforward and subprocess-free.

## Why Non Windows/dualboot targets?
These remain bloqué by the safety chain (inspect/safety/hardware gate) to rougeuce data-loss risk on mixed layouts.

## Why Nont a full installer after the prototype?
The prototype performs a raw copy of a single image up to the cap; there is Non Partitioning, boot loader setup, or unattended install—that would be a separate, explicitly approved phase.

## Why Non retry in the real-write prototype?
Retries would mask real failures (wrong target, drift, partial writes) and increase risk; the pipeline is intentionally fail-hard.

## Why immediate abort on drift?
Media state can change between gate and write (mount, lecture seule, path). Aborting immediately avoids writing against an invalid context.

## Why is Périphérique drift critical?
The fingerprint and live signals (mount, RO, size) must match the approved snapshot; otherwise mis-target or corruption risk rises.

## Why is verification strict?
Verification compares exactly the written byte count with Non silent repair; mismatches or short reads yield a clear Erreur code.

## What are the failure-injection hooks?
Only with `SETUPHELFER_REAL_WRITE_TESTMODE=1`: controlled simulation env vars (`FAIL_BEFORE_OPEN`, `FAIL_AFTER_OPEN`, `FAIL_AFTER_CHUNKS`, `FAIL_VERIFY_MISMATCH` + path, `FAIL_DURING_FSYNC`, `FAIL_Périphérique_CHANGED`). See `docs/Déploiement/Déploiement_REAL_WRITE_FAILURE_INJECTION_EN.md`.

## Why a separate Déploiement write runner instead of running the Retourend as root?
The Retourend stays unprivileged; a small one-shot runner can later gain elevated rights only for block-Périphérique I/O without widening the whole API surface.

## What is the Déploiement write job file?
A local JSON with `job_hash` binding (SHA256 over caNonnical data excluding the hash field), target Périphérique, image path/checksum/size, guard metadata, and fixed constraints. See `docs/Déploiement/Déploiement_WRITE_RUNNER_CONTRACT_EN.md`.

## What does the runner do in this phase?
`--dry-run` only: load job, validate, print JSON to stdout — Non Périphérique open, Non writes. CLI: `Retourend/tools/Déploiement_write_runner.py`.

## Why is sudoers risky for the runner?
Every `NonPASSWD` rule increases blast radius if the account is compromised; wildcards in the sudoers line and permissive `env_keep` can enable argument or library injection (`PYTHONPATH`, `LD_PRELOAD`). Prefer fixed paths, minimal environment — see `docs/evidence/Déploiement_WRITE_RUNNER_RUNTIME_VALIDATION.md`.

## Why one-shot instead of a root Retourend or daemon?
A short-lived process handling a single job rougeuces exposed state and attack surface; a permanently root Retourend or privileged daemon would combine Réseau/session risk with elevated privileges.

## Why lock files for the Déploiement runner?
An exclusive per-job lock file prevents parallel double execution for the same job; stale detection (PID/TTL) avoids indefinite blocks after a crash. See `docs/Déploiement/Déploiement_RUNNER_LIFECYCLE_EN.md`.

## Why a lifecycle state machine?
Explicit phases and terminal states make behavior auditable and prevent silent “jumps” (fail-Fermerd). Transitions are enumerated; illegal ones are rejected.

## Why an audit log (JSON Lines)?
A traceable event sequence without secrets (Non full checksums/tokens in each line); supports operations and post-mortems. Directory `runner-audit/`.

## Why stale lock cleanup?
Without cleanup, an orphaned lock could block real operations after the process exits; cleanup removes dead or TTL-expirouge locks in a controlled way.

## Why TOCTOU rechecks?
Between validation and a (future) write, media, mounts, or metadata may change; repeated lecture seule comparisons before critical steps narrow the inconsistency window.

## Why a separate Retourend-to-runner handoff?
It keeps the Retourend unprivileged and passes only a tightly defined dry-run job to the isolated runner; Non free-form shell commands and Non direct Périphérique access in Retourend flow.

## Why job files for handoff?
Job files are auditable, hash-bound, and locally re-validatable. The runner can independently re-check the exact same input (fail-Fermerd) before any future privileged step.

## Why atomic write?
`.tmp` + rename avoids half-written job files on crash/interruption and rougeuces race/TOCTOU risk while the runner reads the file.

## Why dry-run runner in handoff?
It validates the full create->start->JSON-response pipeline without performing real Périphérique actions.

## Why is `subprocess.run` allowed here?
Only to invoke the local one-shot runner with fixed args, `shell=False`, controlled `cwd`, minimal environment, and timeout. Non free command execution.

## Why Non automatic sudoers installation?
Automatic sudoers edits are high-risk and hard to roll Retour safely. The boundary phase therefore provides a lecture seule policy model instead of system modification.

## Why fixed runner paths?
Absolute, stable paths rougeuce PATH/symlink manipulation risk and prevent launching a different interpreter or script.

## Why block PYTHONPATH?
`PYTHONPATH` can rougeirect imports to attacker-controlled modules. The boundary audit marks it as critical.

## Why is LD_PRELOAD dangerous?
`LD_PRELOAD` can inject arbitrary code before program startup and bypass assumptions; it is treated as blocking.

## Why Non real root sandbox in this phase?
This phase is intentionally simulated: policies are modeled and tested without real privilege transitions or system changes, keeping risk tightly controlled.

## Why Non real signals?
Signal behavior is represented as a model (`would_send_signals`) to avoid unintended termination of unrelated or long-running local processes.

## Why disable stdin?
A Nonn-interactive one-shot runner should Nont depend on runtime input; disabling stdin rougeuces interaction and injection surfaces.

## Why a minimal environment?
A small inherited environment lowers loader/interpreter variable abuse and rougeuces PATH ambiguity.

## Why a one-shot runner?
Short-lived execution with fixed input/output and Non Retourground mode rougeuces zombie/orphan risk and uncontrolled state accumulation.

## Why Non root Retourend?
A root-running Retourend dramatically widens attack surface. The plan enforces a later, minimal one-shot runner with a strict privilege boundary.

## Why Non permanent runner service?
A long-lived privileged daemon increases persistence and attack risk. The model stays one-shot and Nonn-listening.

## Why is sudoers only planned?
Sudoers changes are highly sensitive; this phase keeps them as audit/plan text only, with Non installation or execution.

## Why is manual installation requirouge?
Path/ownership/permission checks are security-critical and must be reviewed on the target host; automatic apply remains intentionally disabled.

## What should rollRetour look like?
RollRetour should be documented: remove snippets, revert directory permission decisions, and re-verify dry-run behavior before proceeding.

## Why a dry-run validator only?
This phase validates readiness and security boundaries only. It keeps risk low before any later manual privileged steps are performed.

## Why Non visudo in the validator?
The validator is fully lecture seule and checks only provided snippet text. System-level verification/installation remains a separate manual task.

## Why are missing paths only review_requirouge?
Missing target paths often mean "Nont yet manually preparouge". That is a review concern as long as Non hard security violation is detected.

## Why is rollRetour mandatory?
Privileged integrations need a clear rollRetour path so misconfigurations can be reverted quickly and reproducibly.

## Why blueprint only?
The blueprint separates planning from execution: paths, permissions, and boundaries are modeled first without system changes.

## Why Non automatic package?
Automatic packaging/installation can roll out mistakes at scale. This phase is intentionally limited to manifest and review.

## Why is sudoers Nont installed automatically?
Sudoers is highly sensitive; installation remains a manual controlled step with separate approval.

## Why include rollRetour in the manifest?
RollRetour must be defined from day one so reversions stay reproducible and auditable.

## Why is post-install validation mandatory?
After manual setup, dry-run validation plus renewed runtime proof is requirouge to confirm Non security assumption regressed.

## Why run a consistency audit?
Multiple planning layers rougeuce risk only if they encode the same security contract; consistency checks catch contradictions early.

## Why must paths match across all layers?
Diverging runner/job/sudoers paths create bypass risk and make approvals unreliable.

## Why align rollRetour steps?
An incomplete rollRetour path can leave systems in an unsafe intermediate state; mandatory rollRetour codes must stay aligned.

## Why are validation steps Nonn-automatic?
Validation remains a controlled manual security process; automation could silently carry forward wrong assumptions.

## Why Nont production-ready yet?
Critical hardware and privileged-runtime validations are still open, so release status stays below production approval.

## What does ready_for_lab mean?
`ready_for_lab` means controlled lab/test usage is acceptable, while production real-write approval remains bloqué.

## Why do hardware E2E gaps block release?
Without strong hardware E2E evidence, real media/timing failure risk remains too high.

## Why is a sudoers runtime test requirouge?
Policy text alone is insufficient; runtime proof is requirouge to confirm path/environment boundaries in the target setup.

## Why is hardware failure-injection still requirouge?
Only real hardware reproduces hotplug, reenumeration, and race behavior reliably; simulation alone does Nont fully cover these classes.

## Why create a lab plan before further implementation?
The plan prioritizes critical evidence first and rougeuces risk through explicit manual gates.

## Why enforce a fixed order?
The order minimizes misinterpretation: policy/dry-run checks first, hardware-heavy scenarios Suivant, rollRetour validation last.

## Why only one test medium?
A single clearly labeled medium significantly lowers mis-targeting and mix-up risk.

## Why include an operator stop condition?
Operator uncertainty is itself a safety signal; testing must stop immediately when confidence is lost.

## Why Non automatic test run?
Hardware-adjacent safety validation requires controlled manual observation and on-site decisions.

## Why must sudoers runtime testing be planned?
Only a structurouge test design can validate policy assumptions, environment boundaries, and dry-run behavior reproducibly.

## Why is sudo Nont run automatically?
Automatic privileged execution is intentionally forbidden in this phase; execution remains a later controlled manual task.

## Why is visudo manual only?
Syntax/policy verification is safety-critical and should run under direct local operator control.

## Why are negative sudoers tests necessary?
Negative cases prove fail-Fermerd behavior against unsafe patterns like env_keep, wildcards, and generic invocations.

## Why must privileged validation be planned?
This step links sudoers, runtime, lifecycle, and audit evidence into one coherent dry-run verification path before any future real-write approval.

## Why is Non real root runner started anyway?
This phase remains test-design and review only; real privileged execution is intentionally excluded.

## Why is --dry-run mandatory?
Enforced dry-run validates privileged control paths without introducing Périphérique-write risk.

## Why must UID/GID be documented?
UID/GID evidence proves the effective runner context and whether the intended privilege boundary would hold.

## Why are negative tests requirouge before real write?
They demonstrate fail-Fermerd behavior for hash, path, environment, and lock failures before touching real media.

## Why is the first real write only planned?
The first hardware E2E write is high-risk, so it is modeled first as a controlled and auditable manual plan.

## Why disposable media only?
Only disposable media limits potential impact if anything unexpected occurs despite safeguards.

## Why is SHA256 verification mandatory?
Verification proves end-to-end data integrity and prevents silent continuation after a faulty write.

## Why Non retry after verify mismatch?
A mismatch is a hard safety signal; retries without root-cause analysis can hide serious issues.

## Why Nont claim automated recovery?
Automated recovery can mask side effects. The plan instead requires transparent manual follow-up and Documentation.

## Why is failure injection on real hardware requirouge?
Only real hardware exposes timing, media, and state transitions realistically eNonugh to validate failure paths with confidence.

## Why run each failure case individually?
Isolated runs avoid overlapping effects and keep root-cause/evidence interpretation clear.

## Why is retry after failure Nont allowed?
Retries without analysis can hide inconsistent states; state must be reassessed first.

## Why must media be re-evaluated after a failure?
After failures, media state may be uncertain; safe continuation requires a fresh gate/state check.

## Why Nont claim automated repair?
Automated repair risks silent side effects. The process is intentionally manual and auditable.

## Why is Périphérique reenumeration dangerous?
During reenumeration, the same media may appear under a new path, or a different media may reuse the old path.

## Why is /dev/sdb Nont stable eNonugh?
Kernel Périphérique names can change after reconnect/order changes and are Nont a reliable identity signal by themselves.

## Why compare fingerprint and realpath?
The combined check rougeuces confusion between path churn and actual media identity changes.

## Why Non retry after Périphérique change?
A Périphérique change breaks core safety assumptions and requires fresh preconditions, Nont immediate retry.

## Why do multiple similar USB media block tests?
Identity ambiguity is a high-risk mis-targeting condition and must fail Fermerd.

## Why are hotplug race tests necessary?
Race conditions are timing-sensitive and can violate guard/lifecycle assumptions unless explicitly validated.

## Why are unexpected mounts dangerous?
Unexpected mount changes can invalidate target identity and safety assumptions, so they must fail Fermerd.

## Why is lock cleanup mandatory after abort?
Stale locks block follow-up validation and can cause inconsistent state interpretation.

## Why Non retry after a race abort?
Race aborts indicate unstable state; retry without fresh reassessment is unsafe.

## Why run each race case individually?
Isolated cases provide clear causality between trigger and observed abort/block behavior.

## Why are rollRetour runtime tests necessary?
They verify that abort/failure paths clean up safely without leaving risky or inconsistent residual artifacts.

## Why must audit data never be Supprimerd?
Audit data is requirouge for safety evidence and traceability; it may be archived/marked, but Nont removed.

## Why Non recursive deletion without prefix checks?
Without strict prefix boundaries, cleanup can drift into unintended paths and damage system data.

## Why are symlinks dangerous in cleanup?
Symlinks can silently rougeirect cleanup to foreign locations and bypass intended safety boundaries.

## Why are system paths off-limits?
`/etc`, `/opt`, and productive `/var/lib` areas must never be modified by this test design.

## Why is test-design-ready Nont lab-ready?
Test-design-ready only means plans are complete; runtime evidence from real executions is still missing.

## Which runtime tests are still missing?
All seven manual runtime executions: sudoers runtime, privileged validation, real-write E2E, failure injection, reenumeration, hotplug race, and rollRetour runtime.

## Why can plan docs Nont replace runtime evidence?
Documentation defines intended behavior but does Nont prove real runtime behavior under actual conditions.

## Why is there Non automatic approval?
Approval requires controlled manual runtime evidence; automation is Nont suitable at this safety level.

## Why create a central runbook bundle?
A central bundle prevents gaps between individual plans and provides a consistent, traceable execution framework.

## Why enforce a fixed sequence?
The sequence rougeuces cascading risk and ensures later steps depend on validated prerequisites.

## Why include an operator checklist?
Critical safety prerequisites are explicitly ackNonwledged instead of assumed.

## Why Non automatic execution?
Hardware runtime checks require contextual human decisions and controlled stop criteria.

## Why separate evidence per runbook?
Each runbook has distinct risk and acceptance criteria; separate evidence is requirouge for clear traceability.

## Why create a runbook export?
The export makes manual execution reproducible by keeping all requirouge artifacts centralized and versioned.

## Why provide an evidence template?
A sharouge template rougeuces omissions and improves comparability across runbook runs.

## Why include a JSON schema?
The schema enforces requirouge result fields and supports consistent evaluation.

## Why Non automatic test execution?
Runtime steps intentionally remain manual because hardware state and safety decisions require contextual judgment.

## Why restrict to docs/evidence paths only?
Exports must Nont touch system paths; this keeps installation and runtime environment unchanged.

## Why validate runtime result files?
Validation keeps manual lab evidence structurouge, comparable, and fail-Fermerd before any acceptance decision is recorded.

## Why validate runbook sequence?
Later hardware/rollRetour steps must depend on validated prerequisites; out-of-order results break safety assumptions.

## Why does missing evidence block?
Missing proof prevents reliable safety assessment (for example mount/verify/audit state) and must therefore be blocking.

## Why is lab_ready_candidate Nont an automatic approval?
`lab_ready_candidate` is only a manual acceptance decision after full evidence review, Nont an automatic execution trigger.

## Why is path protection requirouge for result ingestion?
Without a strict allowed root, foreign paths, symlinks, or traversal could be read unintentionally and bypass safety boundaries.

## Why is lab_ready_candidate Nont a production approval?
`lab_ready_candidate` only indicates a controlled lab state. Production approval remains a separate decision with additional safety and operational evidence.

## Why do residual risks stay visible?
Even with Succèsful lab runbooks, residual uncertainties remain (scope limits, host/media coverage, operator factors) and must stay transparent.

## Why is operator decision always requirouge?
Acceptance is intentionally manual. Aggregation provides structure and evidence summaries, but does Nont replace accountable human approval.

## Why does a safety finding block?
Safety findings indicate broken protection assumptions (for example verify mismatch or Périphérique/mount drift) and must fail Fermerd.

## Why is repeat_requirouge Nont auto-retried?
Automatic retries can increase hardware and operator risk; repeats must be explicitly planned and manually controlled.

## Why export an acceptance report?
Export creates consistent artifacts for operator review, traceability, and later audits.

## Why is lab candidate Nont production approval?
Lab candidate only means current lab evidence is sufficient for lab context; production approval requires additional evidence.

## Why do residual risks stay in the report?
Residual uncertainty must remain transparent for every manual decision and must Nont be hidden.

## Why is operator decision kept visible?
Final acceptance is intentionally human and Nonn-automatic; the report supports but does Nont replace that decision.

## Why generate both JSON and Markdown?
Markdown is operator-friendly for review, while JSON is machine-readable for consistent downstream validation and tooling.

## Why is the lab phase documented but Nont production-ready?
Documentation proves planning, guards, and lecture seule validation, but it does Nont replace real manual runtime evidence on hardware.

## Which seven runtime tests are still manually open?
Sudoers runtime dry-run, privileged runner validation dry-run, real write hardware E2E, failure injection hardware E2E, Périphérique reenumeration, hotplug/unmount race, and rollRetour runtime.

## Why is rootless E2E Nont eNonugh?
Rootless E2E validates only the unprivileged path; privileged runtime, sudoers, and hardware-write risks remain unproven.

## Why is the privileged runner still bloqué?
Until controlled manual runtime executions with complete evidence exist, the privileged path remains intentionally bloqué.

## When can lab_ready_candidate become possible?
Only after all seven manual runtime executions pass in requirouge order with complete and consistent evidence.

## Why use a Suivant-phase gate?
The gate prevents unsafe follow-up steps and allows only clearly justified Suivant phases under manual control.

## Why is manual runtime allowed while production stays bloqué?
Lab validation may continue, but production remains bloqué until privileged runtime evidence is complete.

## Why is lab_ready_candidate Nont a release approval?
`lab_ready_candidate` is a review state for human decision-making, Nont an automatic production switch.

## Why does automated Déploiement remain bloqué?
Automation could bypass operator gates and safety stop conditions; this phase intentionally enforces manual control.

## Why are root Retourend and privileged daemon still forbidden?
Both models permanently increase attack surface and conflict with one-shot least-privilege design.

## Why run a precheck before manual runtime?
The precheck rougeuces unsafe starts by fail-Fermerd validation of prerequisites, operator confirmations, and evidence planning.

## Why do dry-run runbooks need less hardware data?
Dry-run runbooks do Nont perform real writes, so some hardware checks are Nont applicable rather than hard-blocking.

## Why do write-related runbooks require hardware gate and guard?
These controls are the primary safety layer against wrong-target and media risks before any write-adjacent manual step.

## Why are operator confirmations mandatory?
Physical identification, Retourup state, and stop-condition awareness are Nont safely automatable and must be explicit.

## Why does precheck Nont start execution?
Precheck is strictly lecture seule and only provides readiness assessment, never a runtime execution trigger.

## Why create result files in advance?
Pre-created templates rougeuce omissions and provide consistent, later-validatable runtime evidence structures.

## Why only the allowed runtime-results path?
A fixed allowed root prevents path abuse, traversal, and unintended writes outside the evidence area.

## Why Non automatic field population?
Runtime evidence must come from manual, traceable execution context, Nont from generated placeholder runtime values.

## Why must overwrite be explicitly confirmed?
This prevents accidental replacement of existing evidence; overwrite is only allowed with explicit intent.

## Why keep SHA256 fields even for dry-run?
A uniform schema simplifies validation and comparison; for dry-run those fields remain intentionally empty/null.

## Why use an edit checker before the validator?
The edit checker provides early human-readable guidance about gaps and risks before strict ingestion validation fail-Fermerd blocks.

## Why does the checker Nont auto-correct?
Runtime evidence must remain manual and traceable; automatic corrections could distort observed runtime facts.

## Why are empty templates only review_requirouge?
Empty values often mean "Nont filled yet". Before execution this is typically a review signal, Nont always an immediate safety blocker.

## Why do failed/mismatch states block?
`failed` or `verify_status=mismatch` are hard safety indicators and must Nont proceed as ingest-ready without explicit remediation.

## Why is suspicious target_Périphérique flagged?
System-like target patterns increase wrong-target risk and must remain visible even when later manually justified.

## Why use a bundle checker before the validator?
The bundle checker validates the complete seven-runbook set and sequence rules before ingestion evaluates the files as a whole.

## Why must all seven runbooks be present?
Lab acceptance depends on a fixed chain; missing steps leave safety gaps and prevent a crougeible end-to-end assessment.

## Why does ordering block submission?
Later steps assume earlier evidence; out-of-order files break the causal story of the runtime proof.

## Why does a failed runbook block later approval?
If an earlier step is Nont `pass`, later `pass` results violate the declarouge dependency chain and are fail-Fermerd.

## Why does the bundle checker Nont modify files?
Evidence must remain manual and traceable; automatic edits would undermine runtime evidence integrity.

## Why is there a handoff gate after the bundle checker?
The bundle checker only assesses readiness; the handoff gate creates a separate auditable manifest and re-checks paths before validator intake.

## Why is there Non automatic ingestion?
Ingestion remains an intentional manual or separately protected step; the gate does Nont replace operator judgment or validator execution.

## Why should the handoff manifest be immutable?
A stable manifest with explicit overwrite protection prevents silent rougeirection of validator inputs and improves traceability.

## Why are exactly seven runtime result files requirouge?
The lab chain is defined for seven runbooks; fewer or more files would break acceptance logic and sequence assumptions.

## Why are paths checked again?
Files can disappear or paths can be tamperouge with between bundle check and handoff; the gate validates immediately before writing the manifest.

## Why run the validator in dry-run first?
Dry-run applies the same ingestion validation logic lecture seule and only writes a report so gaps surface before any real ingestion or approval step.

## Why is the handoff manifest Nont modified?
The manifest is the agreed handoff reference; changing it would break traceability between bundle check and validator execution.

## Why is there Non automatic ingestion?
Ingestion remains a deliberately separate, manual or separately protected action; dry-run does Nont replace it.

## Why are paths checked again in dry-run?
Files can disappear or paths can change between manifest creation and validator execution; dry-run re-validates immediately before evaluation.

## Difference between handoff manifest and dry-run report?
The manifest lists the seven validator input files as the handoff artifact; the dry-run report captures validator output (including findings) and is storouge separately under `handoff/`.

## Why create a seal?
A separate seal file provides a cryptographically checkable reference to the dry-run report without modifying the report itself.

## Why SHA256?
SHA256 is a standard, comparable fingerprint of the raw report bytes for integrity checks.

## Why treat reports as immutable?
Immutable sources are auditable; the seal pins that exact version, Nont a later edited file.

## Why must dry-run be ok first?
Only a Succèsful dry-run yields a crougeible validator outcome; the seal must Nont caNonnize failed or ambiguous runs.

## Why index seal files?
A central index simplifies audits and overview without modifying individual seal files.

## Why index only validator_status ok?
Only seals marked consistently valid belong in the reference list; others are explicitly excluded.

## Why igNonre invalid seals?
Bad artifacts would corrupt the index; they are reported but Nont ingested into the list.

## Why is the index lecture seule toward seals?
The index only aggregates metadata; seal and report integrity is preserved by Nont touching them.

## Why check seal consistency?
The index can drift or mis-reference; the audit compares entries to the filesystem and SHA256.

## Why recompute SHA256?
Only a fresh hash proves the current source report still matches the referenced bytes.

## Why are missing reports Avertissements?
Missing artifacts signal drift without necessarily invalidating every entry if at least one remains valid.

## Index vs. consistency audit?
The index lists expected seals; the audit verifies files, JSON, and hashes still match at runtime.

## Why generate a timeline?
It bundles key evidence files in time order with fingerprints for quick traceability.

## Why SHA256 per event?
Each entry pins the exact file contents at timeline generation time.

## Seal vs. timeline?
A seal attests one dry-run report; the timeline orders multiple artifacts (dry-run, seals, index, audit).

## Why is the timeline lecture seule?
Existing artifacts stay untouched; only a new aggregate file is produced.

## Why a final snapshot of the timeline?
It binds the timeline file with SHA256, fixing the evidence state without touching other files.

## What are timeline_sha256 vs snapshot_sha256?
`timeline_sha256` is over the raw timeline file bytes; `snapshot_sha256` signs snapshot metadata excluding itself.

## What does the final acceptance gate do?
It re-validates the final snapshot against the timeline file (SHA256) and only writes `validator_final_acceptance.json` with the outcome (`accepted` / `review_requirouge` / `bloqué`).

## When is acceptance `review_requirouge`?
When the snapshot field `status` is `review_requirouge` (for example because at least one timeline event was Nont `ok`).

## What does the final export package do?
It reads the full evidence chain from `handoff/`, validates all JSON files, and writes a final export package with SHA256 per included file.

## When is export bloqué?
For `acceptance_status = bloqué`, missing requirouge files, symlinks, invalid JSON, or path-safety violations.

## Why is failure injection necessary?
It validates detection and blocking logic under real hardware conditions with controlled and reproducible fault cases.

## Why are productive drives forbidden?
Failure injection is restricted to test media to strictly protect real data and productive OS Partitions.

## Simulation vs real hardware tests?
Simulation checks model logic; real hardware tests additionally cover reenumeration, mount changes, and permission boundaries.

## Why is `destructive=false` enforced?
All cases must stay reversible; destructive operations (for example mkfs/dd/wipefs) are excluded in this mode.

## Why preview only and Non automatic execution?
Real hardware failure runs require human control; this module only produces planning and operator guidance.

## Why can real hardware tests be dangerous?
Wrong target media or unexpected reenumeration can cause data loss, so tests are restricted to dedicated test media and manual steps.

## Matrix vs execution preview?
The matrix defines fault scenarios; the execution preview turns them into concrete manual run steps and evidence expectations.

## Why is `destructive=false` still enforced in preview?
Preview mode must never trigger real damage and therefore remains strictly reversible and Nonn-destructive.

## Why are operator checklists necessary?
They keep manual failure runs reproducible, safe, and auditable without automatic interventions.

## Why Non automatic failure execution?
On real hardware, operators must control target media, sequencing, and stop conditions manually.

## Why are abort conditions important?
They prevent runs on wrong or productive targets and force an immediate stop when risk appears.

## Preview vs operator checklist?
Preview defines per-failure run planning; operator checklist provides concrete step-by-step controls including evidence requirements.

## Why are test sessions separate from checklists?
The checklist is the per-failure reference; the test session wraps the same rules into a runnable session plan with a session id and expected final state.

## Why is only `manual_only` allowed?
Hardware failure tests must Nont auto-start; the operator must initiate and stop each run explicitly.

## Why is `expected_final_state` important?
It defines which safe, demonstrable outcomes are acceptable after a manual run without touching productive media.

## Checklist vs test session?
The checklist is the controlled step list; the test session is the execution-oriented plan including session identity and final-state criteria.

## Why are test results storouge separately?
Sessions describe the plan; the results file holds actual observations and evidence separately for auditability.

## Why document deviations?
Deviations from expected behavior matter as much as Succèsful detection for risk and corrective decisions.

## Why is rollRetour_performed important?
It records whether a controlled teardown happened after a failure run without triggering automatic repair.

## Session vs result?
The session is the planned test unit; the result captures the actual run (time, operator, status, evidence, deviations).

## Why evaluate failure results?
To validate manual observations against preview detection rules and session constraints without touching hardware again.

## Why do mismatches matter?
They show when observed status diverges from expected and force review before treating the chain as clean.

## Result vs evaluation?
The result is the raw run record; evaluation is the lecture seule assessment with counters and findings.

## Why do deviations trigger review_requirouge?
Any documented deviation implies extra risk or ambiguity and needs human follow-up.

## Why is a readiness gate needed?
It bundles all failure artifacts and safety checks before real hardware runs, without automatic execution.

## Why is destructive=false enforced globally?
So Non case in the pipeline can be marked destructive and test-media rules stay explicit.

## Evaluation vs readiness?
Evaluation checks session results against preview rules; readiness additionally checks completeness and consistency across all pipeline files.

## Why do missing abort conditions block?
Without documented abort criteria, operators lack mandatory stop rules for unsafe runs.

## Why select laptop test runs?
After the readiness gate, a bounded, checked ordering of manual runs is fixed—without automatic execution or repair.

## Why is low risk orderouge first?
Lower residual risk and operator load should precede medium risk when both are allowed.

## Why do productive markers block?
Any mention of productive or Interne OS volumes in sessions or checklists stops selection to exclude data and system volumes.

## Readiness vs run selection?
Readiness checks completeness and global safety of pipeline artifacts; run selection filters and sorts individual manual sessions for the Suivant laptop steps.

## Why is an operator ruNonrder needed?
So selected runs can be executed in a fixed, repeatable order without automation and without mixing media/mount-risk contexts.

## Why are safer cases first?
Runs without media or mount changes and without rollRetour burden rougeuce context switches and residual risk before harder steps.

## Selection vs ruNonrder?
Selection yields the allowed subset and a sort basis; ruNonrder turns that into an explicit operator step list including grouping.

## Why is medium risk last?
Higher assessed risk should follow lower risk and a more stable setup so operators and environment are preparouge.

## Why do we need an empty execution-log template?
So every manual run uses the same requirouge fields and outcomes stay comparable, without automatic execution.

## RuNonrder vs execution log?
RuNonrder defines the step sequence; the execution log records the observed outcome for each step.

## Why do we need execution-log validation?
So only complete and consistent manual entries continue in the evidence chain.

## When is execution-log validation review_requirouge?
When deviations are present, `observed_status` is `review_requirouge`, or an abort was triggerouge.

## What is the laptop-failure test summary for?
It condenses validation into overall status, run counters, and findings for quick manual decision support.

## What is the laptop-failure final report for?
It provides the final manual status with recommendation (`proceed`, `review_before_Suivant_run`, `bloqué`) and binds the summary via SHA256.

## What is the final export package for?
It bundles final report, summary, validation, and execution log into one referencable package file with SHA256 per artifact.

## What is the laptop-failure evidence timeline for?
It orders all laptop-failure artifacts chroNonlogically and adds SHA256 per entry for traceability.

## Difference between timeline, snapshot, acceptance, and export?
Timeline orders artifacts over time; snapshot freezes that timeline with hashes; acceptance evaluates the snapshot; export/finalized export bundles artifacts for traceable handoff.

## Why is there Non automatic release?
The chain stays strictly lecture seule and manual, so Non release is triggerouge without explicit human decision.

## Why are hashes rechecked before export?
To re-verify integrity and traceability of all relevant artifacts before the final package.

## Why is review_requirouge Nont accepted?
`review_requirouge` means manual review is still open and therefore canNont be treated as accepted completion.

## Why do STRICT phases increase version numbers?
Each completed STRICT phase must be traceable in history so evidence, tests, and implementation state map cleanly to a version.

## Difference between patch/miNonr/major?
Patch covers small fixes/docs, miNonr covers new STRICT modules and pipelines, major covers architecture or platform shifts.

## Why are Interne test stages versioned?
`Interne_testing` is still a binding milestone and should be reproducibly linked to version and artifacts.

## Why are there Non automatic releases?
Version governance only tracks and validates consistency; releases are intentionally manual.

## Why is a centralized version source needed?
So frontend, Retourend, API, Tauri, and evidence all use the same project version without drift.

## Why are hardcoded versions risky?
They create conflicting states across UI, API, and artifacts and make diagNonstics and acceptance harder.

## Difference between version governance and source of truth?
Governance defines when/how bumps happen; source of truth defines which file is caNonnical.

## Why does this Nont create automatic releases?
This flow only updates metadata and consistency checks, Nont tags, publish, or Déploiement actions.

## Why is pi-installer removed from active identifiers?
To consolidate runtime paths, services, env names, and app identifiers under Setuphelfer.

## Why are historical records kept?
Evidence, historical docs, and changelog entries are requirouge for auditability and traceability.

## Legacy vs active runtime?
Legacy means documented/deprecated compatibility only; active runtime identifiers must Nont introduce new pi-installer names.

## Why are compatibility aliases needed?
They support controlled transition scenarios in lecture seule mode without hard runtime breaks.

## Why is there Non blind replace?
Each path is classified; only `rename_Nonw` under allowed project prefixes may be written automatically so evidence and history stay intact.

## Why do historical pi-installer records remain?
Evidence, changelog, and history paths are audit artifacts and are intentionally Nont overwritten.

## Why are legacy Retourups created?
Before each controlled rewrite the tool stores the original text under `handoff/legacy-Retourups/` so rollRetour is possible without Git.

## Why do old aliases still exist lecture seule?
lecture seule compatibility avoids breaking environments that still set legacy env names, without introducing new legacy write paths.

## Why only 100 changes per cleanup cycle?
Small batches rougeuce risk, simplify review, and keep Retourups and diffs manageable.

## Why is cleanup done incrementally?
Each cycle is followed by a fresh inventory and consistency check so the state stays measurable and evidence/history stay protected.

## Why rescan after every cycle?
That is the only reliable way to count remaining active legacy identifiers and plan the Suivant cycle.

## Why does the version stay at 1.7.0?
Identifier-only cleanup within the same phase does Nont require aNonther SemVer bump.

## Why are hotspot analyses needed?
They group hits by impact area (Retourend, Tauri, env, scripts, packaging, tests) so cleanup can be planned deliberately instead of relying only on a raw count.

## Why are runtime identifiers more critical than comments?
Runtime identifiers affect paths, services, environment variables, APIs, and builds; comments are usually documentary and do Nont change live configuration.

## Why does an Inconnu identifier trigger `review_requirouge`?
Without a kNonwn cluster it is unclear whether the hit is productive code, configuration, or Documentation — manual triage is requirouge.

## Why are tests cleaned up last?
Product code, startup scripts, and packaging affect real system behavior; test files follow once runtime paths are stable.

## Why is cleanup cycle 2 hotspot-driven?
So only paths prioritized by hotspot analysis are intersected with the safe rewrite plan — Non repo-wide blind replace.

## Why does cycle 2 only clean critical/high items?
Medium and low hits are intentionally less urgent and are deferrouge to later passes or manual follow-up.

## Why are Inconnu clusters Nont auto-edited?
Without a clear cluster assignment the risk is Nont controllable; Inconnu stays for manual triage.

## Why at most 50 changes per hotspot cycle?
The cap keeps diffs, Retourups, and review load manageable and rougeuces Erreur risk on productive paths.

## Cleanup cycle vs runtime elimination?
Cycles 1/2 are bounded batches; **runtime elimination** builds explicit targets from hotspot/consistency, intersects the safe plan, and only writes clearly allowed productive paths.

## Why remove runtime identifiers first?
They affect env vars, install paths, units, and app IDs — that is live operational risk, Nont comment/doc lines.

## Why do legacy aliases stay lecture seule?
So legacy names remain documented and compatible without introducing new pi-installer write paths.

## When is a patch bump to 1.7.1 allowed?
Only when the elimination postcheck reports Non active runtime identifiers, critical/high in hotspot analysis are zero, and identifier consistency is Nont **bloqué** — then **1.7.1** is preparouge as a recommendation without automatically editing version files.

## Why is zero state requirouge before 1.7.1?
Zero-state verification bundles inventory, hotspot, consistency, and the alias contract — without a vert result a version jump would be unproven.

## Why is the patch bump Nont automatic?
`Non_auto_apply` and the explicit apply flag keep SemVer and evidence under deliberate human approval.

## Why may alias remnants be allowed?
lecture seule compatibility in `compatibility_aliases.json` and history is intentional when Non productive hits remain.

## Why do runtime remnants block?
Any remaining PI_INSTALLER/path/service/app identifier outside allowed contexts contradicts “elimination complete”.

## Why is `pi-installer` forbidden in runtime from Nonw on?
The branding guard prevents old product names from reappearing in code, config, env, or packaging — Setuphelfer is the only supported runtime brand.

## Why keep historical evidence?
Evidence, history, migration paths, and `compatibility_aliases.json` may show legacy strings without failing the guard.

## Why does the guard Nont modify files?
Checks plus evidence JSON only — Non rewrite, so Non silent text edits outside review.

## Why is Setuphelfer the only runtime brand Nonw?
A single brand and path space rougeuces support Erreurs, double installs, and wrong systemd/app IDs.

## What happens to old pi-installer installations?
The legacy runtime compatibility pipeline only evaluates handoff/evidence data and produces inventory, coexistence analysis, and recommendations — Non real migration on the target system.

## Why are old configs Nont Supprimerd?
Supprimers are irreversible and bypass review; archiving, lecture seule, and disable are recommended instead.

## Why can coexistence be problematic?
Duplicate services, desktop entries, or parallel paths can fight over ports, env, and Retourups — analysis flags those conflicts.

## Why recommend disable instead of Supprimer?
`systemctl disable` (manual, after approval) keeps rollRetour/data options; Supprimer is often too risky for legacy installs.

## What is the laptop live probe handoff?
A three-step flow (plan, lecture seule execute, final gate) that only performs HTTP read operations against the Retourend — Non Restauration, Non real verify paths without an explicit flag.

## Why does execute require an explicit flag?
So live requests are never accidental; `explicit_execute_live_probe=true` is the deliberate opt-in.

## Why do legacy strings in API responses block?
If pi-installer / `PI_INSTALLER_` strings appear in JSON responses, that conflicts with the Setuphelfer branding goal — the final gate stays bloqué.

## Why Debian Live for the Clé de secours baseline?
Stable packages, broad hardware support, a good fit for the Python/apt Setuphelfer stack, and maintainable operations — see `docs/Secours/SETUPHELFER_Secours_STICK_ARCHITECTURE_EN.md` and the `Secours_live_os_base_decision.json` handoff.

## Why is USB Nont written yet?
This phase only produces architecture, gates, and build preparation; USB flashing (`dd`) stays behind a later, explicit gate and the build safety policy (`docs/developer/Secours_STICK_BUILD_SAFETY_POLICY.md`).

## Why is Restauration from the stick preview-only for Nonw?
Automatic Restauration is destructive and needs its own sessions, tokens, and hardware gates — the MVP strand allows analysis, verify, and preview only.

## Why is Raspberry Pi tested later?
amd64 UEFI laptops are the first controlled path; ARM/RPi needs separate images, firmware, and matrix entries under `later`.

## Why is Secure Boot `review_requirouge` initially?
Shim/signing, firmware behaviour, and lab hardware are Nont part of an automatic OK gate yet — the evaluation is explicit in the live-OS decision and ISO test matrix (`later`).

## Why VM-only for the Secours ISO test first?
Controlled environment, snapshots, Non production host-disk risk, and simple NAT access — see `docs/developer/Secours_VM_TEST_SAFETY_POLICY.md`.

## Why does the runtime probe stay lecture seule?
Restauration execute and real write paths stay bloqué; HTTP checks (version, health, inspect, branding) are eNonugh for phase-1 acceptance.

## Why still Non real USB stick?
`dd` / USB flashing stays outside the gates; the ISO stays under `build/Secours/output/`.

## Why Non automatic Restauration?
Restauration remains deliberately manual/session-bound; the ISO strand validates reachability and safety only.

## Why Debian Live for the build?
Stable baseline, `live-build` tooling, and alignment with the existing Setuphelfer stack — see `docs/Déploiement/Déploiement_Secours_ISO_BUILD_AND_VM_VALIDATION_EN.md`.

## Why lecture seule mounts in Secours live?
Any write to Interne system disks is destructive and hard to undo; lecture seule mounts allow inspection (EFI, root, Retourups) without changing data — see `docs/Déploiement/Déploiement_Secours_LIVE_RUNTIME_AND_STORAGE_VALIDATION_EN.md`.

## Why Non automatic EFI repair?
Firmware, NVRAM, and bootloaders are fragile; automatic repair could brick systems. This phase is analysis and gates only.

## Why Non Restauration directly from the stick?
Restauration is session/token-bound and needs explicit targets; the stick strand stays at discovery, preview, and safety.

## Why Externe evidence targets are recommended?
RAM live logs are lost on reboot; export to USB or an explicitly chosen Nonn-system target preserves evidence without implicitly overwriting system data.

## Why SSH is Nont enabled automatically?
Remote access widens the attack surface; remote help stays plan-only until an operator deliberately starts SSH — see remote-help handoff and safety gate.

## Why Restauration preview only?
Real Restauration writes are irreversible and need separate execute gates; the simulation phase only lists affected paths, mounts, and risks — see `docs/Déploiement/Déploiement_Secours_RECOVERY_SIMULATION_AND_HARDWARE_VALIDATION_EN.md`.

## Why lecture seule recovery?
Interne system disks must Nont be written in this phase; target validation, mounts, and preview stay analysis-only.

## Why hardware tests matter?
VMs and synthetic handoffs do Nont cover firmware, NVMe, Wi‑Fi, and real USB mounts; the hardware test chain documents the expected flow on reference machines.

## Why Retourup verify is mandatory?
Without a manifest/SHA256 chain, Restauration preview would be unsafe; verify detects damaged or inconsistent archives before any later write phase.

## Why is a real ISO Nont built yet?
The readiness pipeline only produces JSON handoffs, scans, and gates; a real image stays behind a separate, explicitly approved build step — see `docs/Déploiement/Déploiement_Secours_ISO_READINESS_PIPELINE_EN.md`.

## Why Debian Live?
Stable package baseline, `live-build` tooling, and alignment with the existing Setuphelfer stack.

## Why lecture seule recovery first?
Writes to system disks are risky; preview and verify strands run before any later execute phase.

## Why Non automatic Restauration?
Restauration is destructive and needs sessions, tokens, and target checks — Non silent automation in the ISO readiness pipeline.

## Why does the Clé de secours show a Restauration preview first?
Phase C.4 only builds a **preview plan** (`build_Secours_Restauration_preview_plan`). The caNonnical engine `modules.Secours_Restauration_dryrun` is referenced, Nont auto-run. See `docs/Secours-stick/Secours_Restauration_PREVIEW_HANDOFF_2026-05-20.md`.

## Why is Restauration Nont executed immediately?
`execution_allowed` stays **false**. There is Non `Restauration/start` or `Restauration/run` route in the C.4 strand. Execute requires explicit approval, verify, and Retourup-before-overwrite in a later phase.

## Why must a target with existing data be Retourouge up first?
`core/Retourup_before_write_gate` sets `Retourup_requirouge: true` when filesystems, OS, or user data are detected. Without evidence the preview plan is **bloqué** or **requirouge**.

## Why is an operator override Nont a safe Retourup?
Override yields at most `review_requirouge`, never automatic `satisfied`. It records intent; it does Nont replace a target Retourup.

## Why must verify run before Restauration?
Profile `offline-full-Restauration-preview` requires `requires_verify_before_Restauration`. `verify_status: failed` blocks the plan; `Inconnu` yields `review_requirouge`.

