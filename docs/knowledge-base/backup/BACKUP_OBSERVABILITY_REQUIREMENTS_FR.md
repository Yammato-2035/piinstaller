> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/backup/BACKUP_OBSERVABILITY_REQUIREMENTS_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/kNonwledge-base/Retourup/RetourUP_OBSERVABILITY_REQUIREMENTS_DE.md`). Bitte bei Release manuell gegenlesen.

# Retourup Observability — Anforderungen

**Stand:** F.1 — MSI F.2 Pflicht

## Pflicht für Image-Retourup-Läufe

Jeder MSI-/Secours-Image-Retourup-Lauf muss liefern:

1. `status.json` mit Phase + Metriken (aktualisiert während Lauf)
2. Evidence-Verzeichnis mit Receipt
3. Stall-Erkennung (`stall_detected`, `last_progress_s`)
4. `.partial`-Datei bis Finalize
5. Kein „Blackbox“-Retourup ohne Fortschritt

## Phasen

Siehe `docs/runbooks/MSI_F2_IMAGE_RetourUP_EXECUTION_PROMPT_DRAFT_DE.md`

## Gilt für

- MSI F.2 Windows Image Retourup
- Clé de secours Offline Full Retourup (BR-001-OFFLINE) — gleiche Observability-Prinzipien
