# Rescue Developer QEMU Lab Profile

Explicit overlay for QEMU smoke tests only. **Not** used for public rescue builds.

- Dev Server URL: `http://10.0.2.2:8000` (QEMU user NAT → host)
- QEMU host fallback enabled
- German keyboard/locale in manifest
- Local VNC bind `127.0.0.1` only (planned for next smoke)
- SSH forward disabled by default

Standard developer profile (`profiles/developer`) keeps `127.0.0.1` for real hardware.
