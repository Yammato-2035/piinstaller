# G513QM Hybrid Graphics Contract

## Binding

- `device_binding`: `asus_rog_gabriel`
- Expected DMI product substrings: `G513QM`
- CPU vendor: AMD (Ryzen 5800H class)
- Graphics mode: **hybrid**
- Display GPU preference: **AMD iGPU** (internal panel)
- Discrete GPU role: **NVIDIA PRIME render offload** (not forced as sole display path)

## Driver expectations

| Stack | Expectation |
|-------|-------------|
| AMD | `amdgpu` KMS for display/X11/installer |
| NVIDIA proprietary | Single ABI branch when available; PRIME offload |
| Nouveau | Profile-specific fallback only |
| Secure Boot | Detect only — never modify / no MOK enroll |
| Windows NVMe write | **forbidden** |
| Automatic install | **forbidden** |

## PCI IDs

Real PCI IDs must come from physical capture (`lspci -nnk`). Until then:

```text
pci_devices: pending_physical_capture
```

Do not invent Renoir/GA106 device IDs from the marketing model name alone.

## Profiles (see `config/rescue/g513qm_graphics_profiles.json`)

1. Hybrid Auto — AMD display, NVIDIA may load, capture on
2. AMD Safe Display — preferred installer fallback
3. NVIDIA Proprietary Diagnostic — no auto installer
4. Nouveau Fallback Diagnostic — no auto installer
5. Basic Graphics Emergency — `nomodeset` last resort
6. Capture Only / Text — max diagnostics

## Live vs post-install NVIDIA

Mint 22.2 live kernel on stick: `6.14.0-29-generic`. Matching `linux-headers-6.14.0-29-generic` were **not** available in configured apt indexes at rebuild time; therefore proprietary NVIDIA **modules for that exact live kernel** are not prebuilt on the stick. Live NVIDIA recognition uses inventory + Nouveau diagnostic profile; proprietary branch ships as offline pack for **installed** system / later kernel match.
