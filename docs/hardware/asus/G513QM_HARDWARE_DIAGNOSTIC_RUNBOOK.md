# G513QM Hardware Diagnostic Runbook

Cursor must not claim hardware diagnostics as done until the operator runs them.

## MyASUS / MyASUS in WinRE

Check: memory, SSD/NVMe, display, fans, motherboard/system, GPU/graphics if offered.

## RAM

Full MemTest pass — **at least one complete pass**; prefer several. Do not call RAM OK after minutes.

## NVMe (read-only)

```bash
smartctl -a /dev/nvme0n1
nvme smart-log /dev/nvme0n1
nvme error-log /dev/nvme0n1
```

No firmware update in this phase. Never write partitions.

## Windows / WinRE stability

Document: reliable Windows boot? freeze under load? WinRE freeze? graphics glitches? internal vs external display.

## Status JSON

Update `docs/evidence/rescue/g513qm-kernel-abc/hardware_diagnostic_status.json` only with operator results.
