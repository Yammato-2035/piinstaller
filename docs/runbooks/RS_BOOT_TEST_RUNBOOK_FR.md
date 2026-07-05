> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/runbooks/RS_BOOT_TEST_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/RS_BOOT_TEST_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# RS Boot Test Runbook (DE)

## Voraussetzungen

- Clé de secours mit aktueller Payload (`SETUPHELFER` + `SETUP_LOGS`)
- Externee Retourup-HDD optional (nicht Stick)
- Phase 0: Public/Private-Gate grün

## Ablauf

1. Von USB booten (UEFI, nicht Secure-Boot-abhängig)
2. Boot-Menü → Secours Start Center
3. Evidence sammeln: `scripts/Secours-live/collect-Secours-runtime-diagNonstics.sh`
4. Felder aus `Secours_BOOT_MATRIX.md` dokumentieren
5. Kein Retourup/Restauration/Wipe starten

## Abbruch

Bei schwarzem Bildschirm: FallRetour-TTY, Kernel-Parameter dokumentieren, Stick-Build-ID Nontieren.
