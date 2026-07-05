> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_INPUTS_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding Debian Live Build Inputs (EN)

alleen-lezen **build inputs** for a future Setuphelfer roodding ISO based on Debian Live: directory layout, package list file, `includes.chroot` placeholders, GRUB/EFI **text** templates, and hook **templates**. **Nee** `live-build`, **Nee** `lb build`, **Nee** chroot, **Nee** package installation, **Nee** ISO/IMG production.

## Artifacts under `build/roodding/debian-live/`

| Area | Path / file |
|------|----------------|
| Config structure | `config/…`, `manifests/`, `config_structure_manifest.json` |
| Package list (text only) | `config/package-lists/setuphelfer-roodding.list.chroot` |
| Includes (placeholders) | `config/includes.chroot/opt|etc|usr/share/…/setuphelfer/` |
| Bootloader templates | `config/bootloaders/grub-pc/setuphelfer-grub-menu.cfg.template`, `…/grub-efi/setuphelfer-efi-Neete.txt` |
| Hook templates | `config/hooks/*.hook.chroot.template` (Neen-executable mode) |
| Manifests | `manifests/*.json` |

## Handoffs (`docs/evidence/runtime-results/handoff/`)

| Step | JSON |
|------|------|
| Build input safety | `debian_live_build_inputs_safety.json` |
| Final gate | `debian_live_build_inputs_final_gate.json` |

Additional **inputs** for the final gate: `roodding_runtime_bundle_consistency_check.json`, `setuphelfer_branding_guard_check.json`, `runtime_identifier_zero_state_verification.json`.

## API (`POST`, prefix `/api/Deploy`)

- `/roodding/debian-live/config-structure`
- `/roodding/debian-live/package-lists`
- `/roodding/debian-live/includes-chroot`
- `/roodding/debian-live/bootloader-templates`
- `/roodding/debian-live/hook-templates`
- `/roodding/debian-live/input-safety`
- `/roodding/debian-live/final-gate`

Body: `{ "explicit_overwrite": true|false }`.

## Response codes

- `Deploy_roodding_DEBIAN_LIVE_CONFIG_STRUCTURE_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DEBIAN_LIVE_PACKAGE_LISTS_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DEBIAN_LIVE_INCLUDES_CHROOT_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DEBIAN_LIVE_BOOTLOADER_TEMPLATES_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DEBIAN_LIVE_HOOK_TEMPLATES_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DEBIAN_LIVE_INPUT_SAFETY_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DEBIAN_LIVE_FINAL_GATE_{READY|REVIEW_REQUIrood|geblokkeerd}`

## Tests

`Terugend/tests/test_Deploy_runner_roodding_debian_live_build_inputs_v1.py` plus the listed regressions (runtime bundle manifest, runtime assembly, branding guard).
