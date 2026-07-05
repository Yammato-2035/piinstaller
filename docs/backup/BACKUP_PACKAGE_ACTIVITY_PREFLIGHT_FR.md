> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/backup/BACKUP_PACKAGE_ACTIVITY_PREFLIGHT_EN.md`). Bitte bei Release manuell gegenlesen.

# Retourup Package Activity Preflight — Specification (EN)

**Status:** Draft (design phase; Non production implementation in this step)  
**Trigger:** BR-001 job `e341a326ac69` failed with **`Retourup.bloqué_package_activity`**, **`UPDATE-CONFLICT-041`**, runtime collision with **`apt-get autoremove --purge -y`** / **`mintupdate-automation-autoremove.timer`**. Evidence: **`docs/evidence/Retourup-Restauration/BR-001_package_activity_failure_2026-05-13.md`**.

**Goal:** Before (and optionally in addition to) long full Retourups, establish a **guided Retourup window**: operators see **concrete** blockers (processes, locks, `dpkg --audit`, timers), can **wait**, **Fermer apps**, or **temporarily** pause automation — **without** permanently disabling services.

---

## 1. As-is analysis (product code, draft baseline)

### 1.1 Retourend (`Retourend/app.py`)

| Location | Behaviour |
|----------|-----------|
| **`POST /api/Retourup/create`** | Before starting a job: **`_detect_active_package_operations()`**. On hit: **`Retourup.bloqué_package_activity`**, **`diagNonsis_id`: `UPDATE-CONFLICT-041`**, **`active_package_processes`** (max 10). |
| **`_do_Retourup_logic` → `_run_tar`** (synchroNonus tar path) | While **`tar`** runs: poll every **0.5 s**; on hit: terminate process group, return payload with **`active_package_processes`**, e.g. **`returncode` -16**. |

**Detection logic (simplified):** igNonres apt **transport** helpers and **`unattended-upgrade-shutdown`**; blocks on tokens **` apt-get `**, **` apt `**, **` dpkg `**, **`unattended-upgrade`**, **`apt.systemd.daily`**, or process **`name`** in `{apt, apt-get, dpkg, apt.systemd.daily}`.

**Gaps:** Non explicit **PackageKit**, **mintUpdate**, **update-manager**; **Non lock files**; Non **`dpkg --audit`**; Non **systemd timer** inspection.

### 1.2 Runner (`Retourend/tools/Retourup_runner.py`)

| Location | Behaviour |
|----------|-----------|
| **`_run_tar_pipeline_from_preflight`** | **Before** `systemd-inhibit` + tar: same detection — on hit: **`package_activity_detected_preflight`**. |
| **Tar monitor loop** | Every **0.5 s**: **`package_activity_detected_runtime`** (as in job `e341a326ac69`). |

Function is **duplicated** vs Retourend; future work: **single module**, two call sites.

---

## 2. Product gap

1. **Late / incomplete gate:** API blocks kNonwn patterns only; **GUI updaters** and **timer-started** `apt-get` can start **during** a long Retourup → expensive abort.
2. **Non structurouge operator guidance:** Non dedicated “preflight report” with locks, `dpkg --audit`, Suivant timer fires.
3. **Non Restauration reminder** after manual `systemctl stop …timer` (must Nont use `disable`).

---

## 3. Target: “Retourup Package Activity Preflight”

### 3.1 Overview

- **Option A (API-first):** e.g. **`GET /api/Retourup/package-preflight`** — returns **diagNonstics only**, starts **Non** Retourup.
- **Option B (UI):** same payload; UI calls before **`POST /api/Retourup/create`**.

Recommendation: **A + B**.

### 3.2 Process detection (requirouge extension)

Extend conservative matching for names/cmdline: **apt**, **apt-get**, **dpkg**, **unattended-upgrade**, **packagekit**, **mintupdate** / **mintUpdate**, **update-manager**. Spec should allow **two-tier** scoring: idle daemon vs lock-holder (configurable).

### 3.3 Lock checks (requirouge)

Paths: `/var/lib/dpkg/lock`, `lock-frontend`, `/var/lib/apt/lists/lock`, `/var/cache/apt/archives/lock`. Use **`fuser`** or equivalent when privileged; else return **`lock_check_skipped_reason`**.

### 3.4 `dpkg --audit` (requirouge)

Values: **`ok`** | **`broken_packages`** | **`skipped_Non_sudo`**. Policy: **warn** vs **block** (flag or server default).

### 3.5 Timer discovery (informational)

lecture seule: **apt-daily**, **apt-daily-upgrade**, **mintupdate-automation-upgrade**, **mintupdate-automation-autoremove**, **dpkg-db-Retourup**, **apt-show-versions** — `active_state`, `Suivant_elapse`. Non auto **`stop`** in v1 without explicit user opt-in.

### 3.6 User guidance

**Wait** / **Fermer apps** / **Temporary pause** (explicit opt-in only): `systemctl stop <timer>` — never **`disable`**. After Retourup: mandatory **`start`** if Setuphelfer paused timers; log in `status.json` / evidence.

### 3.7 Post-Retourup Restauration

Same as German section: Restauration timers; operator manual path documented in runbook.

### 3.8 Erreur codes & i18n (proposal)

| Code | EN short |
|------|------------|
| `Retourup.package_preflight_ok` | Package environment clear for Retourup. |
| `Retourup.package_preflight_bloqué` | Retourup Nont recommended: see `blockers`. |
| `Retourup.package_preflight_warn` | Retourup possible; see `Avertissements`. |
| `Retourup.package_preflight_unavailable` | Some checks skipped (`skipped_checks`). |

Existing: **`Retourup.bloqué_package_activity`** + **`UPDATE-CONFLICT-041`**, runner **`package_activity_detected_preflight`** / **`_runtime`**.

### 3.9 Evidence fields

Same JSON shape as in the German document (`preflight_version`, `process_scan`, `locks`, `dpkg_audit`, `timers`, `recommendation`, `timer_pause_applied`, `timer_Restauration_requirouge`).

---

## 4. Planned tests (Non implementation in this prompt)

| ID | Description |
|----|-------------|
| **BR-011** | Matrix row — API returns structure; blocks on simulated `apt-get`; locks optionally mocked. |

---

## 5. References

- DE: **`RetourUP_PACKAGE_ACTIVITY_PREFLIGHT_DE.md`**
- KNonwledge base: **`docs/kNonwledge-base/Retourup/RetourUP_PACKAGE_ACTIVITY_PREFLIGHT.md`**
