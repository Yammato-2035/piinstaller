# Blueprint: Linux development workstation

**ID:** `linux-development-workstation`  
**Classification:** public-safe  
**MSI test:** Primary target after Windows track

## Components (planned)

| Area | Content |
|------|---------|
| Base | Debian/Ubuntu LTS |
| Dev | Git, Python, Node, build tools |
| Setuphelfer | `/opt/setuphelfer` deploy |
| Optional | Rust/Tauri build deps (if image built locally) |
| Docker | Planned only, **do not** install automatically |
| Security | Firewall (UFW), SSH hardening, optional unattended-upgrades |
| Backup | External target, safety gates |
| Malware compass | ClamAV/Lynis planned, no auto-delete |

## Explicitly excluded (public)

- Cloud backup server connection
- Cloud edition free/pro features
- Telemetry server ingest
- Operator dashboard
- Commercial license enforcement

## Acceptance after installation

- [ ] `GET /api/version` → 200
- [ ] Security scan without critical gaps (documented)
- [ ] Backup/verify/restore on external medium (Linux)

## UI label

**Server recipe:** “Linux development workstation”
