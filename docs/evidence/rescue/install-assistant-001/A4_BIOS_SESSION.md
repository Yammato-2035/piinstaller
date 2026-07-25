# PI-RS-INSTALL-ASSISTANT-001 — Zug A4 BIOS-Session (read-only)

## Inhalt

- Katalog ↔ Ist via `rescue_bios_official_compare` (Gabriel: G513QM.335 vs. typisch 331)
- Checkliste DE/EN
- Evidence-Export (`bios_session_evidence_v1`)
- `automatic_flash_allowed: false`, `boot_next_allowed: false`
- Blockiert Mint-Dry-Run **nicht** (`blocks_mint_dry_run: false`)

## API

- `POST /api/rescue/install-assistant/bios/session`
- `POST /api/rescue/install-assistant/bios/session/export`
- `POST /api/rescue/install-assistant/firmware/check-latest`
