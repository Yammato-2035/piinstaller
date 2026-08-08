# BUILD 1.10.6.0 RESULT

- **Status:** `payload_built_verified_local`
- **SquashFS:** `build/rescue/filesystem.squashfs.repacked-1.10.6.0`
- **SquashFS SHA256:** `4521968ef8df2e3d35bc44210e3345a0056cfe595a31472720398d95370b57ec`
- **GRUB SHA256 (generated):** `fcc66db6f32231d0875e57e4732320185d28eedad1649c939199a16bb7cc0ec6`
- **Default GRUB entry:** `ASUS-TUI-BASELINE-HIGHINFO`
- **Payload version inside image:** `1.10.6.0`
- **Contains:** highinfo boot script, orchestrator, driver/firmware gap engine, install readiness, safe remediation
- **USB / Carrier:** **noch nicht geschrieben** — Doppelbestätigung fehlt
- **Boot3:** pending after carrier update

## Verify (local)

| Check | Result |
|-------|--------|
| React rescue shell present | true |
| `setuphelfer-rescue-highinfo-boot` in sbin | true |
| `high_information_boot_orchestrator.py` in payload backend | true |
| VERSION file | `1.10.6.0` |
