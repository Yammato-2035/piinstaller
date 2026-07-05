> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_F3_IMAGE_VERIFY_PROMPT_DRAFT_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI F.3 — Image Verify (Prompt-Entwurf)

**Voraussetzung:** F.2 success

## Prüfungen (read-only)

- SHA256(Image) == dokumentiert
- Manifest konsistent
- Größe/Bytes plausibel
- Tool-Exitcodes
- Keine Writes

## Status

`ok` | `failed` | `review_required` (BitLocker-Struktur)
