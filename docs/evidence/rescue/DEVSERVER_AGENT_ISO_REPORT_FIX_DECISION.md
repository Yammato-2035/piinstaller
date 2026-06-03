# Devserver Agent ISO Report Fix — Decision

**Fix-Variante:** PYTHONPATH + Modulaufruf + Health-Header + TrustedHost local_lab

## 1. PYTHONPATH / Modulaufruf

- **Vorher:** `PYTHONPATH=/opt/setuphelfer-rescue`, `python3 -m backend.devserver_agent.cli`
- **Nachher:** `PYTHONPATH=/opt/setuphelfer-rescue/backend:/opt/setuphelfer-rescue`, Rescue-venv oder `python3 -m devserver_agent.cli`
- **Dateien:** `build/rescue/profiles/developer-qemu/.../setuphelfer-qemu-smoke-autopilot.sh`, `systemd/setuphelfer-dev-agent.service`, `prepare-controlled-live-build-tree.sh`

## 2. Proxy / Host-Header

- **Autopilot:** curl mit `-H "Host: 127.0.0.1:8000"` gegen `/api/dev-server/health` und `/api/version` über Lab-Proxy
- **Backend:** `_get_allowed_hosts()` ergänzt `10.0.2.2` nur bei `install_profile=local_lab` (kein globales Host-Allow)

## 3. Validator

- Prüft `devserver_agent` im Squashfs, PYTHONPATH, Modulaufruf, Host-Header in Autopilot
- Codes: `RESCUE-QEMU-AGENT-IMPORT-001`, `RESCUE-QEMU-PROXY-HOST-001`, `RESCUE-QEMU-AUTOPILOT-CALL-001`

## Bewusst nicht geändert

- Keine Port-/Profil-Neuanalyse
- Kein DCC-UI-Umbau
- Kein QEMU in diesem Lauf
- Kein ISO-Rebuild (Operator folgt)

## Nächster Schritt

Operator: prepare `developer-qemu` → controlled ISO build → Validator Exit 0 → QEMU Smoke
