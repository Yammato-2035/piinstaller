# Devserver Agent Fix — Deploy Result

**Datum:** 2026-06-03  
**HEAD:** `886a098`

## Ergebnis

| Feld | Wert |
|------|------|
| `deploy_exit` | **1** |
| Ursache | `sudo: Ein Passwort ist notwendig` (Agent-Session, kein interaktives Terminal) |
| `/api/version` HTTP 200 | **yes** (vor Deploy-Versuch, unveränderte `/opt`-Runtime) |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| Backend-Fix `10.0.2.2` unter `/opt` sichtbar | **no** (`grep 10.0.2.2` in `/opt/setuphelfer/backend/app.py` leer) |

Artefakt: `devserver_agent_fix_deploy_run_latest.log`

## Status

**blocked**

## Folge

Gemäß STRICT MODE: **STOP** — kein Build-Tree-Clean, kein Prepare, kein ISO-Build, kein QEMU, bis Operator-Deploy in Terminal 6:

```bash
cd /home/volker/piinstaller
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
```

Danach diesen Lauf ab Phase 1 erneut fortsetzen.
