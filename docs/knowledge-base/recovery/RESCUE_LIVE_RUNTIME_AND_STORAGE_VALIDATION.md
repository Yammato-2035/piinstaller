# Rescue — Live runtime & storage validation (KB)

## Kurzüberblick

Diese Phase ergänzt den ISO-/VM-Strang um **Speicher-Discovery**, **read-only-Mount-Validierung**, **EFI/Boot-Analyse** (nur Lesen und Heuristiken), **Evidence-Export** mit explizitem Ziel (Allowlist: Repo-`build/rescue/evidence/export/`, `/media`, `/run/media`), **Remote-Hilfe-Vorbereitung** (`ssh_auto_start: false`) und ein **Safety-Gate**, das die Handoff-JSONs zusammenfasst.

## Handoff-Dateien

Unter `docs/evidence/runtime-results/handoff/` u. a.:

- `rescue_storage_discovery_plan.json` / `rescue_storage_discovery_result.json`
- `readonly_mount_plan.json` / `readonly_mount_result.json`
- `rescue_efi_boot_analysis.json`
- `rescue_evidence_export_plan.json` / `rescue_evidence_export_result.json`
- `rescue_remote_help_plan.json` / `rescue_remote_help_result.json`
- `rescue_live_hardware_matrix.json`
- `rescue_live_runtime_safety_gate.json`

## Verweise

- Deploy DE/EN: `docs/deploy/DEPLOY_RESCUE_LIVE_RUNTIME_AND_STORAGE_VALIDATION_DE.md` / `_EN.md`
- Evidence-Kette: `docs/evidence/DEPLOY_RESCUE_LIVE_RUNTIME_AND_STORAGE_VALIDATION.md`
- FAQ: `docs/faq/BACKUP_RESTORE_FAQ_DE.md` / `_EN.md` (Abschnitt Rescue Live-Runtime)
