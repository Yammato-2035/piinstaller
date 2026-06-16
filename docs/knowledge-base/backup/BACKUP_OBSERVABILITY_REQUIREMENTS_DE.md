# Backup Observability — Anforderungen

**Stand:** F.1 — MSI F.2 Pflicht

## Pflicht für Image-Backup-Läufe

Jeder MSI-/Rescue-Image-Backup-Lauf muss liefern:

1. `status.json` mit Phase + Metriken (aktualisiert während Lauf)
2. Evidence-Verzeichnis mit Receipt
3. Stall-Erkennung (`stall_detected`, `last_progress_s`)
4. `.partial`-Datei bis Finalize
5. Kein „Blackbox“-Backup ohne Fortschritt

## Phasen

Siehe `docs/runbooks/MSI_F2_IMAGE_BACKUP_EXECUTION_PROMPT_DRAFT_DE.md`

## Gilt für

- MSI F.2 Windows Image Backup
- Rettungsstick Offline Full Backup (BR-001-OFFLINE) — gleiche Observability-Prinzipien
