# Deploy — Rescue Debian Live Build Inputs (EN)

Read-only **build inputs** for a future Setuphelfer rescue ISO based on Debian Live: directory layout, package list file, `includes.chroot` placeholders, GRUB/EFI **text** templates, and hook **templates**. **No** `live-build`, **no** `lb build`, **no** chroot, **no** package installation, **no** ISO/IMG production.

## Artifacts under `build/rescue/debian-live/`

| Area | Path / file |
|------|----------------|
| Config structure | `config/…`, `manifests/`, `config_structure_manifest.json` |
| Package list (text only) | `config/package-lists/setuphelfer-rescue.list.chroot` |
| Includes (placeholders) | `config/includes.chroot/opt|etc|usr/share/…/setuphelfer/` |
| Bootloader templates | `config/bootloaders/grub-pc/setuphelfer-grub-menu.cfg.template`, `…/grub-efi/setuphelfer-efi-note.txt` |
| Hook templates | `config/hooks/*.hook.chroot.template` (non-executable mode) |
| Manifests | `manifests/*.json` |

## Handoffs (`docs/evidence/runtime-results/handoff/`)

| Step | JSON |
|------|------|
| Build input safety | `debian_live_build_inputs_safety.json` |
| Final gate | `debian_live_build_inputs_final_gate.json` |

Additional **inputs** for the final gate: `rescue_runtime_bundle_consistency_check.json`, `setuphelfer_branding_guard_check.json`, `runtime_identifier_zero_state_verification.json`.

## API (`POST`, prefix `/api/deploy`)

- `/rescue/debian-live/config-structure`
- `/rescue/debian-live/package-lists`
- `/rescue/debian-live/includes-chroot`
- `/rescue/debian-live/bootloader-templates`
- `/rescue/debian-live/hook-templates`
- `/rescue/debian-live/input-safety`
- `/rescue/debian-live/final-gate`

Body: `{ "explicit_overwrite": true|false }`.

## Response codes

- `DEPLOY_RESCUE_DEBIAN_LIVE_CONFIG_STRUCTURE_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_PACKAGE_LISTS_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_INCLUDES_CHROOT_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_BOOTLOADER_TEMPLATES_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_HOOK_TEMPLATES_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_INPUT_SAFETY_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`

## Tests

`backend/tests/test_deploy_runner_rescue_debian_live_build_inputs_v1.py` plus the listed regressions (runtime bundle manifest, runtime assembly, branding guard).
