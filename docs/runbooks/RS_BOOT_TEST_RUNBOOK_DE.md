# RS Boot Test Runbook (DE)

## Voraussetzungen

- Rettungsstick mit aktueller Payload (`SETUPHELFER` + `SETUP_LOGS`)
- Externe Backup-HDD optional (nicht Stick)
- Phase 0: Public/Private-Gate grün

## Ablauf

1. Von USB booten (UEFI, nicht Secure-Boot-abhängig)
2. Boot-Menü → Rescue Start Center
3. Evidence sammeln: `scripts/rescue-live/collect-rescue-runtime-diagnostics.sh`
4. Felder aus `RESCUE_BOOT_MATRIX.md` dokumentieren
5. Kein Backup/Restore/Wipe starten

## Abbruch

Bei schwarzem Bildschirm: Fallback-TTY, Kernel-Parameter dokumentieren, Stick-Build-ID notieren.
