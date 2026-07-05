> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/hardware-tests/MSI_LINUX_BLUEPRINT_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/hardware-tests/MSI_Linux_BLUEPRINT_TEST_PLAN_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Linux Blueprint Testplan

**Nach:** Windows Retourup + Verify + Restauration-Evidence + Wipe-Freigabe  
**Blueprint:** `Linux-development-workstation` (public-safe)

## Ziel

MSI als zweiter Linux-Development-Rechner:

1. Debian/Ubuntu LTS installieren (Operator, separater Lauf)
2. Setuphelfer Déploiementen (`/opt/setuphelfer`)
3. Blueprint `Linux-development-workstation` anwenden
4. Systemhärtung prüfen (Firewall, SSH, Updates)
5. Malware-Kompass (ClamAV/Lynis — keine Auto-Löschung)
6. Linux Retourup → Verify → Restauration auf Externeem Ziel testen

## Abnahme Linux-Strang

| Kriterium | Evidence |
|-----------|----------|
| Setuphelfer API 200 | `/api/version` |
| Firewall aktiv/plausibel | security scan/status |
| SSH gehärtet | security configure Evidence |
| Retourup Externe | BR-001-konform |
| Verify OK | Manifest + SHA256 |
| Restauration-Test OK | separater Testdisk |

## Nicht in Public Repo

- Cloud Edition Features
- Telemetrie-Server-Ingest
- Kommerzielle Blueprints (`commercial-*`)

## Malware-Kompass

- Kein eigener Virenscanner behauptet
- Externee Tools nur ausführen/prüfen (ClamAV, Lynis, optional rkhunter)
- Keine Quarantäne ohne Nutzerfreigabe
