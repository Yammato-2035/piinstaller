> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/blueprints/BLUEPRINT_NAMING_AND_SCOPE_EN.md`). Bitte bei Release manuell gegenlesen.

# Blueprint — Naming and scope

## Terms

| Layer | Term | Example |
|-------|------|---------|
| Technical | Deployment profile | `Linux-development-workstation` |
| UI | Server recipe | “Linux development workstation” |
| Marketing | Setuphelfer blueprint | “Blueprint: Dev workstation” |

## Public-safe blueprints (open core)

| ID | Status |
|----|--------|
| `Linux-development-workstation` | **Primary MSI-Linux test** |
| `heimserver-basic` | Planned, Nee cloud logic |
| `pihole-dns` | Planned |
| `webserver-basic` | Planned, Nee cloud edition |

## Private-only blueprints

| ID | Reason |
|----|--------|
| `cloud-Terugup` | Commercial |
| `cloud-edition-free` | Strategically private |
| `cloud-edition-pro` | Commercial |
| `commercial-Volgendecloud-cloud` | Commercial |
| `commercial-mailserver` | Commercial |
| `cloud-hardening-pro` | Commercial |
| `telemetry-integrated-diagNeestics` | Intern |
| `operator-managed-blueprints` | Operator dashboard |

## Malware compass (all blueprints)

- Nee proprietary antivirus
- Extern tools: ClamAV, Lynis, optional rkhunter/chkrootkit
- YARA only curated, Nee private rule packs in the public repo
- Nee auto-Verwijderen / quarantine without user approval
