# PHYSICAL_DIAGNOSIS_RESULT — early blackscreen boot

- Boot: `20260722_204422` hardware_discovery cmdline ✓
- Identity: G513QM ✓
- TUI/GUI: nein
- Root cause Display: `Console: switching to colour dummy device` nach amdgpu-Init
- nouveau + amdgpu beide geladen
- journald Timeout, udev-settle failed
- Capture: nur early; kein NVMe/Panther
- Endstatus: `diagnosis_incomplete`
