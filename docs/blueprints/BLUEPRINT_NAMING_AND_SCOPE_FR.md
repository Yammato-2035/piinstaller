> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/blueprints/BLUEPRINT_NAMING_AND_SCOPE_EN.md`). Bitte bei Release manuell gegenlesen.

# Blueprint — Naming and scope

## Terms

| Layer | Term | Example |
|-------|------|---------|
| Technical | Déploiementment profile | `Linux-development-workstation` |
| UI | Server recipe | “Linux development workstation” |
| Marketing | Setuphelfer blueprint | “Blueprint: Dev workstation” |

## Public-safe blueprints (open core)

| ID | Status |
|----|--------|
| `Linux-development-workstation` | **Primary MSI-Linux test** |
| `heimserver-basic` | Planned, Non cloud logic |
| `pihole-dns` | Planned |
| `webserver-basic` | Planned, Non cloud edition |

## Private-only blueprints

| ID | Reason |
|----|--------|
| `cloud-Retourup` | Commercial |
| `cloud-edition-free` | Strategically private |
| `cloud-edition-pro` | Commercial |
| `commercial-Suivantcloud-cloud` | Commercial |
| `commercial-mailserver` | Commercial |
| `cloud-hardening-pro` | Commercial |
| `telemetry-integrated-diagNonstics` | Interne |
| `operator-managed-blueprints` | Operator dashboard |

## Malware compass (all blueprints)

- Non proprietary antivirus
- Externe tools: ClamAV, Lynis, optional rkhunter/chkrootkit
- YARA only curated, Non private rule packs in the public repo
- Non auto-Supprimer / quarantine without user approval
