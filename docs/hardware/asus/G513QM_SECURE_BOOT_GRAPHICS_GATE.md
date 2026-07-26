# G513QM Secure Boot graphics gate

## Policy

`secure_boot_policy = detect_do_not_modify`

No automatic MOK enrollment, no BIOS changes, no Secure Boot toggle from Setuphelfer.

## Capture on next physical run

```bash
mokutil --sb-state || true
bootctl status || true
dmesg | grep -Ei 'secure boot|lockdown|module verification|nvidia' || true
journalctl -k | grep -Ei 'secure boot|lockdown|module verification|nvidia' || true
```

## Status model

| Status | Behaviour |
|--------|-----------|
| `secure_boot_disabled` | Proprietary NVIDIA test allowed; AMD remains display default |
| `secure_boot_enabled_module_trusted` | Same |
| `secure_boot_enabled_nvidia_unsigned` | Continue AMD display; Nouveau diagnostic available; warn; no MOK |
| `secure_boot_state_unknown` | Treat like unsigned caution; AMD Safe preferred |

## Boot impact

Secure Boot must **never** abort standard AMD Safe / Hybrid Auto boot solely because proprietary NVIDIA fails to load.
