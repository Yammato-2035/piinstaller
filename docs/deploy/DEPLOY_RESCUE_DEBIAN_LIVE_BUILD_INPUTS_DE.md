# Deploy — Rescue Debian Live Build Inputs (DE)

Read-only **Build-Eingaben** fuer eine spaetere Setuphelfer-Rescue-ISO auf Basis von Debian Live: Verzeichnisstruktur, Paketlisten-Datei, `includes.chroot`-Platzhalter, GRUB-/EFI-**Text**vorlagen und Hook-**Templates**. **Kein** `live-build`, **kein** `lb build`, **kein** Chroot, **keine** Paketinstallation, **kein** ISO-/IMG-Write.

## Artefakte unter `build/rescue/debian-live/`

| Bereich | Pfad / Datei |
|--------|----------------|
| Konfigurationsstruktur | `config/…`, `manifests/`, `config_structure_manifest.json` |
| Paketliste (nur Text) | `config/package-lists/setuphelfer-rescue.list.chroot` |
| Includes (Platzhalter) | `config/includes.chroot/opt|etc|usr/share/…/setuphelfer/` |
| Bootloader-Vorlagen | `config/bootloaders/grub-pc/setuphelfer-grub-menu.cfg.template`, `…/grub-efi/setuphelfer-efi-note.txt` |
| Hook-Vorlagen | `config/hooks/*.hook.chroot.template` (Modus non-executable) |
| Manifeste | `manifests/*.json` |

## Handoffs (`docs/evidence/runtime-results/handoff/`)

| Schritt | JSON |
|--------|------|
| Build-Input-Safety | `debian_live_build_inputs_safety.json` |
| Final-Gate | `debian_live_build_inputs_final_gate.json` |

Weitere **Eingaben** fuer das Final-Gate: `rescue_runtime_bundle_consistency_check.json`, `setuphelfer_branding_guard_check.json`, `runtime_identifier_zero_state_verification.json`.

## API (`POST`, Prefix `/api/deploy`)

- `/rescue/debian-live/config-structure`
- `/rescue/debian-live/package-lists`
- `/rescue/debian-live/includes-chroot`
- `/rescue/debian-live/bootloader-templates`
- `/rescue/debian-live/hook-templates`
- `/rescue/debian-live/input-safety`
- `/rescue/debian-live/final-gate`

Body: `{ "explicit_overwrite": true|false }`.

## Response-Codes

- `DEPLOY_RESCUE_DEBIAN_LIVE_CONFIG_STRUCTURE_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_PACKAGE_LISTS_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_INCLUDES_CHROOT_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_BOOTLOADER_TEMPLATES_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_HOOK_TEMPLATES_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_INPUT_SAFETY_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`

## Tests

`backend/tests/test_deploy_runner_rescue_debian_live_build_inputs_v1.py` und die genannten Regressionen (Runtime-Bundle-Manifest, Runtime-Assembly, Branding-Guard).
