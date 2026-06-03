# Backend Recovery — Restart Result

**Datum:** 2026-06-03

| Feld | Wert |
|------|------|
| daemon-reload (Agent) | **no** (sudo Passwort) |
| Backend restart (Agent) | **no** |
| Ist-Zustand (Operator-Recovery) | **recovered** |
| Backend active | **yes** |
| Port 8000 listening | **yes** |
| `/api/version` HTTP 200 | **yes** |
| Runtime-Profil | `local_lab` |

**Status:** `recovered`

**Empfehlung Operator:** `sudo systemctl daemon-reload` ausführen, um systemd-Warnung zu beseitigen (auch wenn API bereits antwortet).
