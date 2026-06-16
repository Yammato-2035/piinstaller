# Blueprint — Naming und Scope

## Begriffe

| Ebene | Begriff | Beispiel |
|-------|---------|----------|
| Technisch | Deployment-Profil | `linux-development-workstation` |
| UI | Server-Rezept | „Linux-Entwicklungsrechner“ |
| Marketing | Setuphelfer Blueprint | „Blueprint: Dev Workstation“ |

## Public-safe Blueprints (Open Core)

| ID | Status |
|----|--------|
| `linux-development-workstation` | **MSI-Linux-Test primär** |
| `heimserver-basic` | Geplant, ohne Cloudlogik |
| `pihole-dns` | Geplant |
| `webserver-basic` | Geplant, ohne Cloud Edition |

## Private-only Blueprints

| ID | Grund |
|----|-------|
| `cloud-backup` | Kommerziell |
| `cloud-edition-free` | Strategisch privat |
| `cloud-edition-pro` | Kommerziell |
| `commercial-nextcloud-cloud` | Kommerziell |
| `commercial-mailserver` | Kommerziell |
| `cloud-hardening-pro` | Kommerziell |
| `telemetry-integrated-diagnostics` | Intern |
| `operator-managed-blueprints` | Operator-Dashboard |

## Malware-Kompass (alle Blueprints)

- Kein proprietärer Virenscanner
- Externe Tools: ClamAV, Lynis, optional rkhunter/chkrootkit
- YARA nur kuratiert, keine privaten Regelpakete im Public Repo
- Keine Auto-Löschung / Quarantäne ohne Nutzerfreigabe
