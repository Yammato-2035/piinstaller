> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/RS_BOOT_TEST_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/RS_BOOT_TEST_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# RS Boot Test Runbook (DE)

## Voraussetzungen

- rooddingsstick mit aktueller Payload (`SETUPHELFER` + `SETUP_LOGS`)
- Externe Terugup-HDD optional (nicht Stick)
- Phase 0: Public/Private-Gate grün

## Ablauf

1. Von USB booten (UEFI, nicht Secure-Boot-abhängig)
2. Boot-Menü → roodding Start Center
3. Evidence sammeln: `scripts/roodding-live/collect-roodding-runtime-diagNeestics.sh`
4. Felder aus `roodding_BOOT_MATRIX.md` dokumentieren
5. Kein Terugup/Herstel/Wipe starten

## Abbruch

Bei schwarzem Bildschirm: FallTerug-TTY, Kernel-Parameter dokumentieren, Stick-Build-ID Neetieren.
