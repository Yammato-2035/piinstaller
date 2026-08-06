# FAQ: Hardware Baseline Diagnostics (EN)

Mandatory questions for PI-RS-HW-BASELINE-DIAG-I18N-002. Short, honest answers.

Languages: [Deutsch](HARDWARE_BASELINE_FAQ_DE.md) · [English](HARDWARE_BASELINE_FAQ_EN.md) · [Français](HARDWARE_BASELINE_FAQ_FR.md) · [Nederlands](HARDWARE_BASELINE_FAQ_NL.md)

## 1. Does a green tile mean the hardware is guaranteed fault-free?

No. `no_immediate_issue_detected` only means the short baseline found no immediate issue. It does not replace a long-running test and never guarantees fault-free hardware.

## 2. What does the quick memory test check?

Inventory (`/proc/meminfo`, optional DMI), kernel signals (EDAC/MCE/OOM) and a bounded quick probe (at most 128 MiB or 2% of MemAvailable, hard timeout).

## 3. Why does it not replace a full Memtest?

A full Memtest takes hours and stresses all RAM. The baseline is deliberately short and safe and never starts Memtest86+/memtester automatically.

## 4. What is checked for the CPU?

Platform data (via `cpu_platform_detection`), machine-check/hardware-error messages, thermal/throttling state and a short deterministic quick probe.

## 5. Why is no long CPU stress test started automatically?

Long stress tests (stress-ng/Prime95) create high load and heat. They need operator confirmation and belong to extended tests, not the baseline.

## 6. What is checked for the GPU?

Detection via `gpu_detection`, render nodes, kernel/firmware errors and optional read-only probes (`glxinfo`/`eglinfo`/`vulkaninfo`). No render stress.

## 7. Why can backup still be possible despite a defective GPU?

The baseline gate blocks GUI mode for a red GPU, but not backup automatically. Backup is read-oriented and does not need stable graphics.

## 8. Which HDD values are critical?

SMART overall FAILED, Pending Sectors, Offline Uncorrectable and repeated kernel I/O errors. Reallocated Sectors and CRC errors are yellow warnings.

## 9. What do Pending Sectors mean?

Sectors the drive has marked as problematic that have not yet been remapped. They are a critical finding and prioritise data rescue.

## 10. Which SATA SSD values are checked?

Wear Leveling, Available Reserved Space, Reported Uncorrectable, UDMA CRC, Unexpected Power Loss and TRIM support via sysfs.

## 11. Which NVMe values are critical?

Critical Warning ≠ 0, Available Spare ≤ Threshold, Percentage Used ≥ 100%, Media/Data Integrity Errors and repeated controller resets.

## 12. Why does Setuphelfer not start a SMART self-test automatically?

SMART self-tests can take a long time and load the drive. The baseline only reads existing attributes; self-tests need operator confirmation.

## 13. What happens on a critical storage finding?

Restore and OS installation are blocked by the gate. Backup from the source disk remains possible so data can still be rescued.

## 14. May a flagged disk still be used as a backup target?

No. A red target disk must not be written to. As a source for an emergency backup, a flagged disk remains readable.

## 15. Which tests need later operator confirmation?

Memtest86+, CPU stress, GPU render stress, SMART short/extended self-test. The baseline starts none of these automatically.

## 16. Which data is sent to the telemetry server?

Only redacted summaries (platform class, CPU/GPU vendor class, status counts, issue codes, kernel/payload version).

## 17. Are serial numbers transmitted?

No. Serial numbers, MAC addresses, IP addresses and full EDID data are never transmitted.

## 18. What differences exist between Pi 3, Pi 4 and Pi 5?

They are detected individually via device tree and receive their own boot-media and OS compatibility assessments. Details: `RASPBERRY_PI_3_TO_5_SUPPORT_EN.md`.

## 19. Can a single 64 GB stick contain all operating systems?

No. Setuphelfer uses a catalogue plus bounded cache instead of "everything on the stick". Details: `64GB_CARRIER_ARCHITECTURE_EN.md`.

## 20. When is a physical hardware test required?

Whenever the baseline reports red/yellow, tools are missing (`test_unavailable`), or real-world function (GUI, print, scan, boot) must be confirmed.
