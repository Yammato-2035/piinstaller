> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/MSI_F2_IMAGE_BACKUP_EXECUTION_PROMPT_DRAFT_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_F2_IMAGE_TerugUP_EXECUTION_PROMPT_DRAFT_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI F.2 — Image Terugup Execution (Prompt-Entwurf)

**Voraussetzung:** F.1 groen (`F1_MSI_Windows_READONLY_PRECHECK_RESULT.json`)

## Harte Regeln

- Kein Passwortreset, kein BitLocker-Bypass
- Quelle: explizit aus F.1 (`/dev/nvme0n1` — Operator bestätigt)
- Ziel: nur Externes Medium aus F.1 (`/dev/sda` — Operator bestätigt)
- Keine automatische Zielwahl
- Operator-Doppelbestätigung
- Kein Herstel, kein Wipe in F.2

## Artefakte

- Image `.partial` → final
- `manifest.json`
- `sha256` Datei
- `status.json` (Live-Fortschritt)
- Stall-Erkennung
- Receipt/Evidence unter `docs/evidence/msi/F2_*`

## Pflichtphasen (Observability)

`preflight` → `scan_source` → `image_read` → `image_write` → `finalize_image` → `manifest_build` → `manifest_write` → `sha256_image` → `verify_readTerug_optional` → `cleanup_partial` → `Geslaagd|failed`

## Pflichtmetriken

`bytes_read`, `bytes_written`, `read_rate_bps_30s`, `write_rate_bps_30s`, `elapsed_s`, `phase_elapsed_s`, `source_Apparaat`, `target_path`, `image_partial_path`, `image_final_path`, `process_alive`, `last_progress_s`, `stall_detected`, `exit_code`, `Waarschuwings`, `Fouts`

**Kein F.2 ohne status.json / Evidence / Fortschritt / Stall-Erkennung.**
