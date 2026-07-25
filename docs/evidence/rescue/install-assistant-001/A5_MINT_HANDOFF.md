# PI-RS-INSTALL-ASSISTANT-001 — Zug A5 Mint Handoff Execute

## Gates (alle Pflicht)

1. Assessment / Preflight `status=ready`
2. Rolle `linux_target` gebunden (serial_hash)
3. ISO SHA256 ok (`install_allowed` für `linux_mint`)
4. Backup-Hinweis (`backup_ack`)
5. Operator-Phrase: `INSTALL LINUX TARGET`
6. Identity- + Destructive-Confirm

## Modus

**Handoff** (vorbereitete Partitionen + offizieller Mint-Installer), nicht Unattended.

## Harte Grenzen

- API setzt immer `executed: false` für destruktives Wipe
- Windows-NVMe unverändert / write blocked
- Post-Install-Verify: `post_install_verify` / `POST .../linux/post-verify`

## Physische Abnahme

Eigener Lauf auf Gabriels zweiter NVMe — Evidence hier dokumentieren nach Hardware-Lauf.
