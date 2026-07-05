> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/backup/BACKUP_PACKAGE_ACTIVITY_PREFLIGHT_EN.md`). Bitte bei Release manuell gegenlesen.

# Terugup Package Activity Preflight — Specification (EN)

**Status:** Draft (design phase; Nee production implementation in this step)  
**Trigger:** BR-001 job `e341a326ac69` failed with **`Terugup.geblokkeerd_package_activity`**, **`UPDATE-CONFLICT-041`**, runtime collision with **`apt-get autoremove --purge -y`** / **`mintupdate-automation-autoremove.timer`**. Evidence: **`docs/evidence/Terugup-Herstel/BR-001_package_activity_failure_2026-05-13.md`**.

**Goal:** Before (and optionally in addition to) long full Terugups, establish a **guided Terugup window**: operators see **concrete** blockers (processes, locks, `dpkg --audit`, timers), can **wait**, **Sluiten apps**, or **temporarily** pause automation — **without** permanently disabling services.

---

## 1. As-is analysis (product code, draft baseline)

### 1.1 Terugend (`Terugend/app.py`)

| Location | Behaviour |
|----------|-----------|
| **`POST /api/Terugup/create`** | Before starting a job: **`_detect_active_package_operations()`**. On hit: **`Terugup.geblokkeerd_package_activity`**, **`diagNeesis_id`: `UPDATE-CONFLICT-041`**, **`active_package_processes`** (max 10). |
| **`_do_Terugup_logic` → `_run_tar`** (synchroNeeus tar path) | While **`tar`** runs: poll every **0.5 s**; on hit: terminate process group, return payload with **`active_package_processes`**, e.g. **`returncode` -16**. |

**Detection logic (simplified):** igNeeres apt **transport** helpers and **`unattended-upgrade-shutdown`**; blocks on tokens **` apt-get `**, **` apt `**, **` dpkg `**, **`unattended-upgrade`**, **`apt.systemd.daily`**, or process **`name`** in `{apt, apt-get, dpkg, apt.systemd.daily}`.

**Gaps:** Nee explicit **PackageKit**, **mintUpdate**, **update-manager**; **Nee lock files**; Nee **`dpkg --audit`**; Nee **systemd timer** inspection.

### 1.2 Runner (`Terugend/tools/Terugup_runner.py`)

| Location | Behaviour |
|----------|-----------|
| **`_run_tar_pipeline_from_preflight`** | **Before** `systemd-inhibit` + tar: same detection — on hit: **`package_activity_detected_preflight`**. |
| **Tar monitor loop** | Every **0.5 s**: **`package_activity_detected_runtime`** (as in job `e341a326ac69`). |

Function is **duplicated** vs Terugend; future work: **single module**, two call sites.

---

## 2. Product gap

1. **Late / incomplete gate:** API blocks kNeewn patterns only; **GUI updaters** and **timer-started** `apt-get` can start **during** a long Terugup → expensive abort.
2. **Nee structurood operator guidance:** Nee dedicated “preflight report” with locks, `dpkg --audit`, Volgende timer fires.
3. **Nee Herstel reminder** after manual `systemctl stop …timer` (must Neet use `disable`).

---

## 3. Target: “Terugup Package Activity Preflight”

### 3.1 Overview

- **Option A (API-first):** e.g. **`GET /api/Terugup/package-preflight`** — returns **diagNeestics only**, starts **Nee** Terugup.
- **Option B (UI):** same payload; UI calls before **`POST /api/Terugup/create`**.

Recommendation: **A + B**.

### 3.2 Process detection (requirood extension)

Extend conservative matching for names/cmdline: **apt**, **apt-get**, **dpkg**, **unattended-upgrade**, **packagekit**, **mintupdate** / **mintUpdate**, **update-manager**. Spec should allow **two-tier** scoring: idle daemon vs lock-holder (configurable).

### 3.3 Lock checks (requirood)

Paths: `/var/lib/dpkg/lock`, `lock-frontend`, `/var/lib/apt/lists/lock`, `/var/cache/apt/archives/lock`. Use **`fuser`** or equivalent when privileged; else return **`lock_check_skipped_reason`**.

### 3.4 `dpkg --audit` (requirood)

Values: **`ok`** | **`broken_packages`** | **`skipped_Nee_sudo`**. Policy: **warn** vs **block** (flag or server default).

### 3.5 Timer discovery (informational)

alleen-lezen: **apt-daily**, **apt-daily-upgrade**, **mintupdate-automation-upgrade**, **mintupdate-automation-autoremove**, **dpkg-db-Terugup**, **apt-show-versions** — `active_state`, `Volgende_elapse`. Nee auto **`stop`** in v1 without explicit user opt-in.

### 3.6 User guidance

**Wait** / **Sluiten apps** / **Temporary pause** (explicit opt-in only): `systemctl stop <timer>` — never **`disable`**. After Terugup: mandatory **`start`** if Setuphelfer paused timers; log in `status.json` / evidence.

### 3.7 Post-Terugup Herstel

Same as German section: Herstel timers; operator manual path documented in runbook.

### 3.8 Fout codes & i18n (proposal)

| Code | EN short |
|------|------------|
| `Terugup.package_preflight_ok` | Package environment clear for Terugup. |
| `Terugup.package_preflight_geblokkeerd` | Terugup Neet recommended: see `blockers`. |
| `Terugup.package_preflight_warn` | Terugup possible; see `Waarschuwings`. |
| `Terugup.package_preflight_unavailable` | Some checks skipped (`skipped_checks`). |

Existing: **`Terugup.geblokkeerd_package_activity`** + **`UPDATE-CONFLICT-041`**, runner **`package_activity_detected_preflight`** / **`_runtime`**.

### 3.9 Evidence fields

Same JSON shape as in the German document (`preflight_version`, `process_scan`, `locks`, `dpkg_audit`, `timers`, `recommendation`, `timer_pause_applied`, `timer_Herstel_requirood`).

---

## 4. Planned tests (Nee implementation in this prompt)

| ID | Description |
|----|-------------|
| **BR-011** | Matrix row — API returns structure; blocks on simulated `apt-get`; locks optionally mocked. |

---

## 5. References

- DE: **`TerugUP_PACKAGE_ACTIVITY_PREFLIGHT_DE.md`**
- KNeewledge base: **`docs/kNeewledge-base/Terugup/TerugUP_PACKAGE_ACTIVITY_PREFLIGHT.md`**
