# Hardware Baseline Diagnostics — Rescue Stick

Status: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Languages: [Deutsch](HARDWARE_BASELINE_DIAGNOSTICS_DE.md) ·
[English](HARDWARE_BASELINE_DIAGNOSTICS_EN.md) ·
[Français](HARDWARE_BASELINE_DIAGNOSTICS_FR.md) ·
[Nederlands](HARDWARE_BASELINE_DIAGNOSTICS_NL.md)

Related: [Hardware Compatibility Model (EN)](HARDWARE_COMPATIBILITY_MODEL_EN.md).

> Translation note: This edition is structurally complete and content-aligned.
> A native linguistic final review may still be pending.

## 1. Purpose of the early hardware baseline

The early hardware baseline is a **short, safe risk check** at rescue-system
startup. It scans memory, CPU, GPU, and mass storage for signs of immediate
trouble — before backup, restore, OS installation, or GUI use.

It does not replace Memtest86+, SMART self-tests, or stress benchmarks.
Contract layer: `backend/core/hardware_baseline_contracts.py`.
Orchestration: `backend/rescue/hardware_baseline_orchestrator.py`.

## 2. Traffic-light colours and BaselineStatus vocabulary

| Light (`BaselineSeverity`) | Typical status values (`BaselineStatus`) |
|---|---|
| 🟢 `green` | `no_immediate_issue_detected` |
| 🟡 `yellow` | `degraded`, `review_required`, `extended_test_recommended` |
| 🔴 `red` | `immediate_issue_detected`, `extended_test_required` |
| ⚪ `gray` | `test_unavailable`, `not_tested` |

Status meanings:

| Status | Meaning |
|---|---|
| `no_immediate_issue_detected` | No acute signal in the quick checks; **not** a fault-free guarantee |
| `immediate_issue_detected` | Acute finding (e.g. MCE, critical SMART/NVMe warning, kernel GPU hang) |
| `degraded` | Impaired state; operation may continue but is noteworthy |
| `review_required` | Operator review needed (unclear or conflicting data) |
| `extended_test_recommended` | Longer test recommended; never auto-started |
| `extended_test_required` | Longer test required before critical write operations |
| `test_unavailable` | Tool/sensor missing; check skipped, not “passed” |
| `not_tested` | Subsystem not yet examined |

There is **no** status word such as `healthy`, `ok`, or `passed`. Forbidden
claims live in `FORBIDDEN_BASELINE_CLAIMS`.

## 3. Memory baseline (`memory_baseline_diagnostics.py`)

Additive checks:

1. **Inventory** — `/proc/meminfo`, optional `dmidecode -t memory`
2. **Kernel/HW errors** — EDAC / MCE / OOM signals from `dmesg`
3. **Plausibility** — physically reported vs. kernel-usable capacity
4. **Quick probe** — bounded in-process buffer, at most **128 MiB** or
   **2 % of `MemAvailable`** (whichever is smaller); never a full Memtest,
   never installs `memtester` / `stress-ng` / `rasdaemon`

## 4. CPU baseline (`cpu_baseline_diagnostics.py`)

Builds on `cpu_platform_detection` and adds:

- MCE / hardware-error / lockup / watchdog scan (`dmesg`)
- thermal temperatures and throttling hints (`sysfs`)
- bounded, deterministic quick probe

**Never** `stress-ng`, Prime95, or similar sustained load. No microcode/BIOS
update.

## 5. GPU baseline (`gpu_baseline_diagnostics.py`)

Reuses `gpu_detection.build_gpu_report` as the sole inventory source and adds:

- render nodes (`/dev/dri/renderD*`)
- kernel/firmware errors (hang, reset, fence timeout, Xid)
- optional read-only probes: `glxinfo` / `eglinfo` / `vulkaninfo`

Missing driver/firmware → typically `yellow`/`review_required`. Critical
kernel GPU errors → `red`. No driver install, no modprobe/cmdline writes.

## 6. HDD / SATA-SSD / NVMe baseline

Shared layer: `storage_baseline_diagnostics.py` (kernel I/O errors, tool
availability). Device classes:

| Class | Module | Typical sources |
|---|---|---|
| HDD | `hdd_baseline_diagnostics.py` | `smartctl` attributes (incl. 5/197/198/199/194) |
| SATA-SSD | `sata_ssd_baseline_diagnostics.py` | wear/spare/uncorrectable/CRC, TRIM |
| NVMe | `nvme_baseline_diagnostics.py` | `nvme smart-log` / `nvme id-ctrl` |

Only **existing** SMART/NVMe attributes are read. A SMART self-test
(`smartctl -t`, extended NVMe self-tests) is **never started automatically**.

## 7. Limits of the quick tests

- 🟢 `green` / `no_immediate_issue_detected` does **not** mean hardware is
  fault-free or long-term stable.
- A quick probe covers only a tiny memory/CPU slice.
- Missing tools yield `test_unavailable` / `gray`, not “all good”.
- Extended tests (Memtest86+, SMART self-test, GPU render stress) sit outside
  this quick path.

## 8. `HardwareBaselineGate`

Implementation: `backend/rescue/hardware_baseline_gate.py`.

Fields (additive to `core.safety_facade`, **never** a bypass):

| Field | Role |
|---|---|
| `backup_allowed` | Read-only emergency backup remains generally possible |
| `restore_allowed` | Restore only without red data-critical findings and after full checks |
| `os_installation_allowed` | OS installation analogous to restore |
| `gui_mode_allowed` | GUI only without a red GPU finding |

Both layers must agree: baseline gate **and** `safety_facade`.

## 9. Impact of critical findings

| Finding | Effect |
|---|---|
| Red on memory / CPU / storage (aggregated) | blocks restore and OS installation |
| Red on GPU | blocks GUI (`gui_mode_allowed=false`), **not** backup |
| Red **source** disk | remains backupable (reading is the point of emergency backup) |
| Red **target** disk | never writable for backup destination, restore, or OS installation |

Per-operation evaluation: `evaluate_operation_against_baseline_gate`.

## 10. API routes (read-only / bounded)

Module: `backend/api/routes/rescue_hardware_baseline.py`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/rescue/hardware/baseline/status` | gate/run status or `{has_run:false}` |
| `POST` | `/api/rescue/hardware/baseline/quick` | start quick baseline |
| `POST` | `/api/rescue/hardware/baseline/extended-preview` | same checks, recommendations emphasised |
| `GET` | `/api/rescue/hardware/baseline/latest` | last full run |
| `GET` | `/api/rescue/hardware/baseline/memory` | memory subsystem |
| `GET` | `/api/rescue/hardware/baseline/cpu` | CPU subsystem |
| `GET` | `/api/rescue/hardware/baseline/gpu` | GPU subsystem |
| `GET` | `/api/rescue/hardware/baseline/storage` | all storage results |
| `GET` | `/api/rescue/hardware/baseline/storage/{device_id}` | one device |

No route starts installs, firmware updates, formatting, or SMART self-tests.

## 11. Extended tests require operator confirmation

`ExtendedTestRecommendation.operator_confirmation_required` defaults to
`true`. `/extended-preview` only surfaces recommendations (`memtest86plus`,
`cpu_stress`, `gpu_render_stress`, `smart_self_test_short`, …) and never
starts a long-running test. Every extended test needs an **explicit,
separate operator action** outside this API.

## 12. Privacy

Baseline telemetry follows `telemetry_redaction_contract.py` /
`hardware_dcc_status.py`: **no serial numbers, no MAC addresses, no IP
addresses** in telemetry payloads. Device IDs remain technical block-device
names (e.g. `sda`, `nvme0n1`), not hardware serials.
