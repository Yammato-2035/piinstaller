# Backup Domain Audit — B.1

**Routen:** 32

| Route | Method | Risiko |
|---|---|---|
| `/api/backup/clone` | POST | high |
| `/api/backup/clone/disk-info` | GET/POST | high |
| `/api/backup/cloud/delete` | POST | high |
| `/api/backup/cloud/list` | GET | low |
| `/api/backup/cloud/quota` | GET | low |
| `/api/backup/cloud/test` | POST | medium |
| `/api/backup/cloud/verify` | POST | medium |
| `/api/backup/create` | POST | high |
| `/api/backup/delete` | POST | high |
| `/api/backup/external-targets` | GET | low |
| `/api/backup/jobs` | GET | low |
| `/api/backup/jobs/{job_id}` | GET | low |
| `/api/backup/jobs/{job_id}/cancel` | POST | medium |
| `/api/backup/jobs/{job_id}/evidence` | GET | low |
| `/api/backup/jobs/{job_id}/evidence` | POST | medium |
| `/api/backup/list` | GET | low |
| `/api/backup/profile-preview` | POST | medium |
| `/api/backup/profiles` | GET | low |
| `/api/backup/profiles` | POST | medium |
| `/api/backup/restore` | POST | high |
| `/api/backup/schedule/run-now` | POST | medium |
| `/api/backup/settings` | GET | low |
| `/api/backup/settings` | POST | medium |
| `/api/backup/status` | GET | low |
| `/api/backup/target-check` | GET | low |
| `/api/backup/target-prepare` | POST | high |
| `/api/backup/targets` | GET | low |
| `/api/backup/usb/eject` | POST | medium |
| `/api/backup/usb/info` | GET | low |
| `/api/backup/usb/mount` | POST | high |
| `/api/backup/usb/prepare` | POST | high |
| `/api/backup/verify` | POST | medium |
