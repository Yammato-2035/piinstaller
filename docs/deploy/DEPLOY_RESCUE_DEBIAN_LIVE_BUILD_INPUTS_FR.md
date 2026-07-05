> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_INPUTS_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours Debian Live Build Inputs (EN)

lecture seule **build inputs** for a future Setuphelfer Secours ISO based on Debian Live: directory layout, package list file, `includes.chroot` placeholders, GRUB/EFI **text** templates, and hook **templates**. **Non** `live-build`, **Non** `lb build`, **Non** chroot, **Non** package installation, **Non** ISO/IMG production.

## Artifacts under `build/Secours/debian-live/`

| Area | Path / file |
|------|----------------|
| Config structure | `config/…`, `manifests/`, `config_structure_manifest.json` |
| Package list (text only) | `config/package-lists/setuphelfer-Secours.list.chroot` |
| Includes (placeholders) | `config/includes.chroot/opt|etc|usr/share/…/setuphelfer/` |
| Bootloader templates | `config/bootloaders/grub-pc/setuphelfer-grub-menu.cfg.template`, `…/grub-efi/setuphelfer-efi-Nonte.txt` |
| Hook templates | `config/hooks/*.hook.chroot.template` (Nonn-executable mode) |
| Manifests | `manifests/*.json` |

## Handoffs (`docs/evidence/runtime-results/handoff/`)

| Step | JSON |
|------|------|
| Build input safety | `debian_live_build_inputs_safety.json` |
| Final gate | `debian_live_build_inputs_final_gate.json` |

Additional **inputs** for the final gate: `Secours_runtime_bundle_consistency_check.json`, `setuphelfer_branding_guard_check.json`, `runtime_identifier_zero_state_verification.json`.

## API (`POST`, prefix `/api/Déploiement`)

- `/Secours/debian-live/config-structure`
- `/Secours/debian-live/package-lists`
- `/Secours/debian-live/includes-chroot`
- `/Secours/debian-live/bootloader-templates`
- `/Secours/debian-live/hook-templates`
- `/Secours/debian-live/input-safety`
- `/Secours/debian-live/final-gate`

Body: `{ "explicit_overwrite": true|false }`.

## Response codes

- `Déploiement_Secours_DEBIAN_LIVE_CONFIG_STRUCTURE_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DEBIAN_LIVE_PACKAGE_LISTS_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DEBIAN_LIVE_INCLUDES_CHROOT_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DEBIAN_LIVE_BOOTLOADER_TEMPLATES_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DEBIAN_LIVE_HOOK_TEMPLATES_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DEBIAN_LIVE_INPUT_SAFETY_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DEBIAN_LIVE_FINAL_GATE_{READY|REVIEW_REQUIrouge|bloqué}`

## Tests

`Retourend/tests/test_Déploiement_runner_Secours_debian_live_build_inputs_v1.py` plus the listed regressions (runtime bundle manifest, runtime assembly, branding guard).
