# Backup Package Activity Preflight — Specification (EN)

**Status:** Draft (design phase; no production implementation in this step)  
**Trigger:** BR-001 job `e341a326ac69` failed with **`backup.blocked_package_activity`**, **`UPDATE-CONFLICT-041`**, runtime collision with **`apt-get autoremove --purge -y`** / **`mintupdate-automation-autoremove.timer`**. Evidence: **`docs/evidence/backup-restore/BR-001_package_activity_failure_2026-05-13.md`**.

**Goal:** Before (and optionally in addition to) long full backups, establish a **guided backup window**: operators see **concrete** blockers (processes, locks, `dpkg --audit`, timers), can **wait**, **close apps**, or **temporarily** pause automation — **without** permanently disabling services.

---

## 1. As-is analysis (product code, draft baseline)

### 1.1 Backend (`backend/app.py`)

| Location | Behaviour |
|----------|-----------|
| **`POST /api/backup/create`** | Before starting a job: **`_detect_active_package_operations()`**. On hit: **`backup.blocked_package_activity`**, **`diagnosis_id`: `UPDATE-CONFLICT-041`**, **`active_package_processes`** (max 10). |
| **`_do_backup_logic` → `_run_tar`** (synchronous tar path) | While **`tar`** runs: poll every **0.5 s**; on hit: terminate process group, return payload with **`active_package_processes`**, e.g. **`returncode` -16**. |

**Detection logic (simplified):** ignores apt **transport** helpers and **`unattended-upgrade-shutdown`**; blocks on tokens **` apt-get `**, **` apt `**, **` dpkg `**, **`unattended-upgrade`**, **`apt.systemd.daily`**, or process **`name`** in `{apt, apt-get, dpkg, apt.systemd.daily}`.

**Gaps:** no explicit **PackageKit**, **mintUpdate**, **update-manager**; **no lock files**; no **`dpkg --audit`**; no **systemd timer** inspection.

### 1.2 Runner (`backend/tools/backup_runner.py`)

| Location | Behaviour |
|----------|-----------|
| **`_run_tar_pipeline_from_preflight`** | **Before** `systemd-inhibit` + tar: same detection — on hit: **`package_activity_detected_preflight`**. |
| **Tar monitor loop** | Every **0.5 s**: **`package_activity_detected_runtime`** (as in job `e341a326ac69`). |

Function is **duplicated** vs backend; future work: **single module**, two call sites.

---

## 2. Product gap

1. **Late / incomplete gate:** API blocks known patterns only; **GUI updaters** and **timer-started** `apt-get` can start **during** a long backup → expensive abort.
2. **No structured operator guidance:** no dedicated “preflight report” with locks, `dpkg --audit`, next timer fires.
3. **No restore reminder** after manual `systemctl stop …timer` (must not use `disable`).

---

## 3. Target: “Backup Package Activity Preflight”

### 3.1 Overview

- **Option A (API-first):** e.g. **`GET /api/backup/package-preflight`** — returns **diagnostics only**, starts **no** backup.
- **Option B (UI):** same payload; UI calls before **`POST /api/backup/create`**.

Recommendation: **A + B**.

### 3.2 Process detection (required extension)

Extend conservative matching for names/cmdline: **apt**, **apt-get**, **dpkg**, **unattended-upgrade**, **packagekit**, **mintupdate** / **mintUpdate**, **update-manager**. Spec should allow **two-tier** scoring: idle daemon vs lock-holder (configurable).

### 3.3 Lock checks (required)

Paths: `/var/lib/dpkg/lock`, `lock-frontend`, `/var/lib/apt/lists/lock`, `/var/cache/apt/archives/lock`. Use **`fuser`** or equivalent when privileged; else return **`lock_check_skipped_reason`**.

### 3.4 `dpkg --audit` (required)

Values: **`ok`** | **`broken_packages`** | **`skipped_no_sudo`**. Policy: **warn** vs **block** (flag or server default).

### 3.5 Timer discovery (informational)

Read-only: **apt-daily**, **apt-daily-upgrade**, **mintupdate-automation-upgrade**, **mintupdate-automation-autoremove**, **dpkg-db-backup**, **apt-show-versions** — `active_state`, `next_elapse`. No auto **`stop`** in v1 without explicit user opt-in.

### 3.6 User guidance

**Wait** / **Close apps** / **Temporary pause** (explicit opt-in only): `systemctl stop <timer>` — never **`disable`**. After backup: mandatory **`start`** if Setuphelfer paused timers; log in `status.json` / evidence.

### 3.7 Post-backup restore

Same as German section: restore timers; operator manual path documented in runbook.

### 3.8 Error codes & i18n (proposal)

| Code | EN short |
|------|------------|
| `backup.package_preflight_ok` | Package environment clear for backup. |
| `backup.package_preflight_blocked` | Backup not recommended: see `blockers`. |
| `backup.package_preflight_warn` | Backup possible; see `warnings`. |
| `backup.package_preflight_unavailable` | Some checks skipped (`skipped_checks`). |

Existing: **`backup.blocked_package_activity`** + **`UPDATE-CONFLICT-041`**, runner **`package_activity_detected_preflight`** / **`_runtime`**.

### 3.9 Evidence fields

Same JSON shape as in the German document (`preflight_version`, `process_scan`, `locks`, `dpkg_audit`, `timers`, `recommendation`, `timer_pause_applied`, `timer_restore_required`).

---

## 4. Planned tests (no implementation in this prompt)

| ID | Description |
|----|-------------|
| **BR-011** | Matrix row — API returns structure; blocks on simulated `apt-get`; locks optionally mocked. |

---

## 5. References

- DE: **`BACKUP_PACKAGE_ACTIVITY_PREFLIGHT_DE.md`**
- Knowledge base: **`docs/knowledge-base/backup/BACKUP_PACKAGE_ACTIVITY_PREFLIGHT.md`**
