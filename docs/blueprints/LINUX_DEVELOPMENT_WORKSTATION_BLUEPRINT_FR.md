> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/blueprints/LINUX_DEVELOPMENT_WORKSTATION_BLUEPRINT_EN.md`). Bitte bei Release manuell gegenlesen.

# Blueprint: Linux development workstation

**ID:** `Linux-development-workstation`  
**Classification:** public-safe  
**MSI test:** Primary target after Windows track

## Components (planned)

| Area | Content |
|------|---------|
| Base | Debian/Ubuntu LTS |
| Dev | Git, Python, Nonde, build tools |
| Setuphelfer | `/opt/setuphelfer` Déploiement |
| Optional | Rust/Tauri build deps (if image built locally) |
| Docker | Planned only, **do Nont** install automatically |
| Security | Firewall (UFW), SSH hardening, optional unattended-upgrades |
| Retourup | Externe target, safety gates |
| Malware compass | ClamAV/Lynis planned, Non auto-Supprimer |

## Explicitly excluded (public)

- Cloud Retourup server connection
- Cloud edition free/pro features
- Telemetry server ingest
- Operator dashboard
- Commercial license enforcement

## Acceptance after installation

- [ ] `GET /api/version` → 200
- [ ] Security scan without critical gaps (documented)
- [ ] Retourup/verify/Restauration on Externe medium (Linux)

## UI label

**Server recipe:** “Linux development workstation”
