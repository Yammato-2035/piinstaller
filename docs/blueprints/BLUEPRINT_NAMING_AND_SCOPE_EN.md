# Blueprint — Naming and scope

## Terms

| Layer | Term | Example |
|-------|------|---------|
| Technical | Deployment profile | `linux-development-workstation` |
| UI | Server recipe | “Linux development workstation” |
| Marketing | Setuphelfer blueprint | “Blueprint: Dev workstation” |

## Public-safe blueprints (open core)

| ID | Status |
|----|--------|
| `linux-development-workstation` | **Primary MSI-Linux test** |
| `heimserver-basic` | Planned, no cloud logic |
| `pihole-dns` | Planned |
| `webserver-basic` | Planned, no cloud edition |

## Private-only blueprints

| ID | Reason |
|----|--------|
| `cloud-backup` | Commercial |
| `cloud-edition-free` | Strategically private |
| `cloud-edition-pro` | Commercial |
| `commercial-nextcloud-cloud` | Commercial |
| `commercial-mailserver` | Commercial |
| `cloud-hardening-pro` | Commercial |
| `telemetry-integrated-diagnostics` | Internal |
| `operator-managed-blueprints` | Operator dashboard |

## Malware compass (all blueprints)

- No proprietary antivirus
- External tools: ClamAV, Lynis, optional rkhunter/chkrootkit
- YARA only curated, no private rule packs in the public repo
- No auto-delete / quarantine without user approval
