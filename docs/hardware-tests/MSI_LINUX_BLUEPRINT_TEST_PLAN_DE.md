# MSI Linux Blueprint Testplan

**Nach:** Windows Backup + Verify + Restore-Evidence + Wipe-Freigabe  
**Blueprint:** `linux-development-workstation` (public-safe)

## Ziel

MSI als zweiter Linux-Development-Rechner:

1. Debian/Ubuntu LTS installieren (Operator, separater Lauf)
2. Setuphelfer deployen (`/opt/setuphelfer`)
3. Blueprint `linux-development-workstation` anwenden
4. Systemhärtung prüfen (Firewall, SSH, Updates)
5. Malware-Kompass (ClamAV/Lynis — keine Auto-Löschung)
6. Linux Backup → Verify → Restore auf externem Ziel testen

## Abnahme Linux-Strang

| Kriterium | Evidence |
|-----------|----------|
| Setuphelfer API 200 | `/api/version` |
| Firewall aktiv/plausibel | security scan/status |
| SSH gehärtet | security configure Evidence |
| Backup extern | BR-001-konform |
| Verify OK | Manifest + SHA256 |
| Restore-Test OK | separater Testdisk |

## Nicht in Public Repo

- Cloud Edition Features
- Telemetrie-Server-Ingest
- Kommerzielle Blueprints (`commercial-*`)

## Malware-Kompass

- Kein eigener Virenscanner behauptet
- Externe Tools nur ausführen/prüfen (ClamAV, Lynis, optional rkhunter)
- Keine Quarantäne ohne Nutzerfreigabe
