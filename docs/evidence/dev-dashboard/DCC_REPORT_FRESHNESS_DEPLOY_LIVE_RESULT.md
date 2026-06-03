# DCC Report Freshness — Deploy Live Result

**Datum:** 2026-06-03  
**HEAD:** `e3d7da9`

## Gesamtergebnis

**Status:** `blocked` — **`deploy_failed`** (sudo-Passwort im Agent-Kontext)

| Aussage | Wert |
|---------|------|
| Fix deployed | **no** |
| API live (recent-evidence) | **no** |
| Juni-2026-Berichte live sichtbar | **no** (nicht geprüft) |
| Defaultlimit 5 live | **no** (Workspace: ok) |
| Filter live | **no** |
| release wiederhergestellt | **yes** (war durchgehend release) |
| QEMU ausgeführt | **no** |

## Ursache

`sudo ./scripts/deploy-to-opt.sh` endete mit Exit **1** (`sudo: Ein Passwort ist notwendig`). Ohne Deploy fehlen Backend-Modul und Frontend-dist unter `/opt`.

## Operator-Folgeschritte

1. `sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller`
2. local_lab aktivieren (Dropin `92-install-profile-local-lab.conf.example`)
3. `curl http://127.0.0.1:8000/api/dev-dashboard/recent-evidence | jq`
4. DCC UI `http://127.0.0.1:3001/?window=cockpit` — Evidence-Tab
5. release-Trap wiederherstellen
6. Erneut ingestieren oder dieses Evidence-Paket ergänzen

## Offene Risiken

- Live-DCC zeigt weiter alte Agent-Uploads (30.05.) bis Deploy+UI-Build auf `/opt`.
- QEMU-Smoke sollte erst nach DCC-Live-Verifikation folgen.
