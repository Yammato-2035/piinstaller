# Safety analysis

- No MSI test, payload build, USB write, backup/restore, internal disk mounts
- No new mount engine; reuses `rescue_setup_logs_resolver.resolve_setup_logs`
- Finalizer may request safe SETUP_LOGS mount only; diagnose start does not
- Rejects `/media/volker/...`, internal paths, wrong labels, symlink mounts
- No mkfs/wipefs/parted/sfdisk/sgdisk/dd
- Auto-shutdown remains opt-in and blocked without persistence
- `.partial` ignored by import
- Runtime evidence retained on persistence failure
