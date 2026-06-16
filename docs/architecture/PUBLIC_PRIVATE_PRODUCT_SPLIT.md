# Public / Private Product Split

**Version:** 1.9.0.0 (Planungsstand)  
**Repo:** Public GitHub

## Zwei Produktwelten

### Öffentlich (Open Core + Client)

- Lokaler Setuphelfer (Backend, Frontend, Tauri)
- Rettungsstick-Client, Rescue-ISO-Pipeline (soweit public-safe)
- Backup/Restore/Verify mit Safety-Gates (keine Cloud-Zielserver)
- Public-safe Contracts: Telemetry-Client, Redaction, Opt-in
- Architektur, Runbooks, Evidence **ohne** Secrets
- MSI-Hardware-**Testpläne** (keine Laufwerkswrites im Repo-Lauf)

### Privat / kommerziell (separates Repository geplant)

- Cloud Backup, Cloud Edition Free/Pro
- Telemetrie- und Diagnostik**server**
- Operator-Dashboard (Cloud-Betrieb)
- Lizenz, Billing, Subscriptions
- Kommerzielle Blueprints und Cloud-Härtungsprofile
- Interne Hardware-/Diagnose-Regeln und Malware-Regelpakete
- Plesk-/IONOS-Produktivintegration

## Übergabe-Prinzip

Public Repo enthält:

- **Was** die privaten Module tun (Handoff-Docs)
- **Nicht** wie sie implementiert sind (kein Servercode)
- Stubs/Contracts mit `.example`-Domains
- `check-public-private-boundary.sh` als Commit-Gate

## Naming

| Ebene | Begriff |
|-------|---------|
| Technisch | Deployment-Profil |
| UI | Server-Rezept |
| Marketing | Setuphelfer Blueprint |

Siehe `docs/blueprints/BLUEPRINT_NAMING_AND_SCOPE_DE.md`.
