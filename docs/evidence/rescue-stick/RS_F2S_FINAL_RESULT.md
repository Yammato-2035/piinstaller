# RS-F2S Rettungsstick — Ergebnis

**Stand:** 2026-06-17  
**Status:** `green` (Stick geschrieben + Payload RS-F2S + Verify)

## Stick

| Feld | Wert |
|------|------|
| Gerät | `/dev/sda` (Intenso Ultra Line, 59 G, USB) |
| ESP | `/dev/sda1` — Label `SETUPHELFER` |
| Logs | `/dev/sda2` — Label `SETUP_LOGS` |
| Squashfs SHA256 (RS-F2S) | `1992d67c66df41223d623d4f06fc44bcad054ec95734385044549a0a0b9caf57` |
| Workspace-Version | 1.9.3.0 |

## Enthaltene Fähigkeiten (Payload-Marker)

- Windows/NTFS-Erkennung (`windows_ntfs_detection_contract`)
- Block-Image-Backup-Preflight (`msi_windows_image_backup`)
- Rescue-Backup-API + Storage-Discovery
- Restore-Preview (kein Execute auf MSI in diesem Lauf)
- Lokale Cloud-Ziel-Konfiguration (nur auf Stick, nicht im Public-Repo)
- Rescue React UI mit Boot-Menü-Mockup + Backup-Assistent (Ziellaufwerk HDD/Cloud)

## GUI

- Hintergrund: `assets/rescue/boot-menu/setuphelfer-boot-menu-de.png`
- Menüpunkt **Backup erstellen** → Zielwahl externe HDD oder Cloud (lokal gespeichert)

## Nicht ausgeführt

- Kein MSI-Backup auf diesem Dev-Laptop
- Kein Restore auf MSI
- Keine Cloud-Server-Implementierung im GitHub-Repo

## Nächster Schritt

**RS-F2B:** MSI vom Stick booten → Windows/NTFS read-only → externes Backup-Ziel → Block-Image auf HDD
