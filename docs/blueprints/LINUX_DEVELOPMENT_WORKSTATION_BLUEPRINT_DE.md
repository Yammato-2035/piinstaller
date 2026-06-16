# Blueprint: Linux Development Workstation

**ID:** `linux-development-workstation`  
**Einstufung:** public-safe  
**MSI-Test:** Primäres Ziel nach Windows-Strang

## Komponenten (geplant)

| Bereich | Inhalt |
|---------|--------|
| Basis | Debian/Ubuntu LTS |
| Dev | Git, Python, Node, Build-Tools |
| Setuphelfer | `/opt/setuphelfer` Deploy |
| Optional | Rust/Tauri-Build-Deps (falls Image-Build lokal) |
| Docker | Nur geplant, **nicht** automatisch installieren |
| Sicherheit | Firewall (UFW), SSH-Härtung, unattended-upgrades optional |
| Backup | Externes Ziel, Safety-Gates |
| Malware-Kompass | ClamAV/Lynis geplant, keine Auto-Löschung |

## Explizit ausgeschlossen (Public)

- Cloud Backup Server-Anbindung
- Cloud Edition Free/Pro Features
- Telemetrie-Server-Ingest
- Operator-Dashboard
- Kommerzielle Lizenz-Enforcement

## Abnahme nach Installation

- [ ] `GET /api/version` → 200
- [ ] Security-Scan ohne kritische Lücken (Dokumentation)
- [ ] Backup/Verify/Restore auf externem Medium (Linux)

## UI-Label

**Server-Rezept:** „Linux-Entwicklungsrechner“
