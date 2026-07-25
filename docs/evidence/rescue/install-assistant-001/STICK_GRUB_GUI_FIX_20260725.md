# Stick GRUB + GUI Fix — Gabriel ASUS ROG (2026-07-25)

## Diagnose (SETUP_LOGS `20260725_110023_boot`)

- Gerät: `ROG Strix G513QM_G513QM` / BIOS `G513QM.331`
- Cmdline: **Lab-Auto (GUI, Physical E2E)** mit `setuphelfer_msi_e2e_auto=1`
- Folge: BVR-Phase `sabrent_wait`, `gui.status=starting`, **kein Xorg-Log**
- Ursache: falscher Menüeintrag (MSI-E2E), nicht „fehlende GPU“ allein
- Kein GRUB-Eintrag „Linux-Installation“

## Maßnahme (Stick Write — autorisiert)

- Skript: `scripts/rescue/patch-stick-install-assistant-grub.sh /dev/sda1`
- Ultra Line `SETUPHELFER` (`/dev/sda1`) gepatcht
- Backup: `grub.cfg.prev-pre-install-assistant-20260725T090434Z`
- Marker: `setuphelfer/rescue/install_assistant_grub.json`

## Neues Menü (Default = 0)

1. **Setuphelfer Linux-Installation (Mint Assistent, GUI)** — hybrid-GPU-Flags, `install_assistant=1`, `gabriel_ops_allowed=1`, **kein** MSI-E2E
2. Linux-Installation (Text)
3. grafische Oberfläche (ASUS-sicher)
4. sicherer Textmodus
5. … Diagnose / ASUS Lab …
6. WARNUNG MSI-only: Lab-Auto Physical E2E (demoted)

## Gates

- Stick-Write + `linux_target` Wipe: erlaubt nach Phrase `WIPE LINUX TARGET` + Identität
- Windows-NVMe: weiterhin write/wipe blocked (eigene Phrase nötig)

## Nächster physischer Schritt

Auf Gabriel vom Stick booten (Default-Eintrag), GUI muss X starten; nicht Lab-Auto E2E wählen.
