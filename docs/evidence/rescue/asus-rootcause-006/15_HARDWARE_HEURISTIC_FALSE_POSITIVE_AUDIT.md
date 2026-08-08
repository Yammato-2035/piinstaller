# 15 Hardware Heuristic False-Positive Audit — PI-RS-ASUS-ROOTCAUSE-006B

**Nach Boot2** (`20260808_064943`), Vergleich mit Boot1 (`20260807_221550`).  
Beide Runs: gleiche 11 Findings, Gate `blocked`, `restore_allowed=false`.

## Regel-für-Regel

### 1) `memory.kernel_uncorrected_error` / `cpu.machine_check_detected`

| Feld | Wert |
|------|------|
| Regel-ID | memory/cpu MCE count |
| Quellcode | `memory_baseline_diagnostics.scan_kernel_memory_errors`, `cpu_baseline_diagnostics.scan_kernel_cpu_errors` |
| Alt-Regex | `mce:\|Machine Check` (IGNORECASE) |
| Eingabezeile | `MCE: In-kernel MCE decoding enabled.` |
| Kontext | Kernel bringt MCE-Decoder online — kein Event |
| Alter Status | red → Restore block |
| Tatsächliche Bedeutung | Capability / Decoder enabled |
| Erwarteter Status | informational (`*.mce_decoder_enabled`), `action_blocking=false` |
| Änderung | `core.kernel_event_classification.classify_mce_dmesg` — Info vs corrected vs uncorrected |
| False-Negative-Risiko | niedrig, wenn echte Lines (`Machine check events logged`, `[Hardware Error]`) weiter rot bleiben (Negativtests) |

### 2) `gpu.kernel_error_detected` (MODE2)

| Feld | Wert |
|------|------|
| Regel-ID | gpu hang/reset scan |
| Quellcode | `gpu_baseline_diagnostics.scan_kernel_gpu_errors` |
| Alt-Regex | `fence.*timeout\|drm.*reset` |
| Eingabezeile | `amdgpu … MODE2 reset` |
| Kontext | AMD Init auf G513QM; DRM eDP connected danach |
| Alter Status | red (GUI block; Restore nicht) |
| Tatsächliche Bedeutung | expected initialization reset |
| Erwarteter Status | `gpu.expected_reset` gray/info |
| Änderung | enger Hang/Fail-Match; MODE2 → expected |
| False-Negative-Risiko | mittel bei generischen Resets — daher nur MODE2 als expected; Hang/fence-timeout/fail bleiben kritish |

### 3) `gpu.driver_missing` (NVIDIA 01:00.0)

| Feld | Wert |
|------|------|
| Regel-ID | GPU driver status |
| Quellcode | `gpu_detection.build_gpu_report` + baseline findings |
| Eingabe | cmdline `modprobe.blacklist=nvidia,…` + kein driver_in_use |
| Alter Status | yellow `driver_missing` |
| Tatsächliche Bedeutung | intentional profile suppression (ASUS-TUI-BASELINE) |
| Erwarteter Status | `driver_intentionally_disabled`, `operational_validation=not_tested` |
| Änderung | Blacklist-Parse in `detect_disabling_cmdline_params` / `detect_intentional_driver_blacklist` |
| False-Negative-Risiko | ohne Blacklist bleibt `driver_missing` (Negativtest) |

### 4) `gpu.drm_device_missing` (AMD 06:00.0)

| Feld | Wert |
|------|------|
| Regel-ID | DRM card mapping |
| Quellcode | `build_gpu_report` nutzte `card{idx}` nach Discovery-Order |
| Eingabe | Hybrid: NVIDIA idx0 → card0, AMD idx1 → card1 (existiert nicht) obwohl AMD `card0` hat |
| Alter Status | yellow false positive |
| Änderung | PCI→`/sys/bus/pci/devices/<addr>/drm/cardN` Mapping |
| False-Negative-Risiko | niedrig; Fallback `card{idx}` bleibt |

### 5) `nvme.incomplete_smart_log` (×2)

| Feld | Wert |
|------|------|
| Status | gray — **kein False Positive für Restore** |
| Aktion | unverändert belassen (kein Blocker) |

## Gate-Semantik

- Restore blockiert nur bei data-critical RED (Memory/CPU/Storage), nicht bei MCE-Decoder/MODE2/intentional NVIDIA.
- `HardwareFinding`: optional `confidence`, `action_blocking`, `category`.
- `HardwareBaselineGate.action_impact`: backup/restore/os_install/gpu_gui.

## Nicht behauptet

- Kein `all_hardware_healthy` / `hardware_faults_excluded`.
- NVIDIA operational validation bleibt `not_tested`.
