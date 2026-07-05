> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/blueprints/LINUX_DEVELOPMENT_WORKSTATION_BLUEPRINT_EN.md`). Bitte bei Release manuell gegenlesen.

# Blueprint: Linux development workstation

**ID:** `Linux-development-workstation`  
**Classification:** public-safe  
**MSI test:** Primary target after Windows track

## Components (planned)

| Area | Content |
|------|---------|
| Base | Debian/Ubuntu LTS |
| Dev | Git, Python, Neede, build tools |
| Setuphelfer | `/opt/setuphelfer` Deploy |
| Optional | Rust/Tauri build deps (if image built locally) |
| Docker | Planned only, **do Neet** install automatically |
| Security | Firewall (UFW), SSH hardening, optional unattended-upgrades |
| Terugup | Extern target, safety gates |
| Malware compass | ClamAV/Lynis planned, Nee auto-Verwijderen |

## Explicitly excluded (public)

- Cloud Terugup server connection
- Cloud edition free/pro features
- Telemetry server ingest
- Operator dashboard
- Commercial license enforcement

## Acceptance after installation

- [ ] `GET /api/version` → 200
- [ ] Security scan without critical gaps (documented)
- [ ] Terugup/verify/Herstel on Extern medium (Linux)

## UI label

**Server recipe:** “Linux development workstation”
