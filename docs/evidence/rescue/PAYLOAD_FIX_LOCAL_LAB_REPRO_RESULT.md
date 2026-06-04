# Payload Fix — Local Lab Repro

**Status:** `blocked`

| Prüfung | Ergebnis |
|---------|----------|
| `local_lab` aktiv | **no** — `install_profile=release` |
| `dev_control_enabled=true` | **no** |
| Devserver/Fleet HTTP 200 | **no** (release blockiert) |
| `require_token=false` live belegt | **review_required** — Dropin `90-devserver-local-lab.conf` existiert, aber Profil nicht auf `local_lab` geschaltet |
| Agent CLI `--print-payload`/`--dry-run` | **yes** in `/opt` nach partiellem Sync |
| QEMU in dieser Phase | **no** |

## STOP-Grund

`sudo install …/92-install-profile-local-lab.conf.example` → Passwort erforderlich.

Per Auftrag: **kein Build, kein QEMU** bis `local_lab_ready`.
