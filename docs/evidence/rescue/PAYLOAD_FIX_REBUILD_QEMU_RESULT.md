# Payload Fix Rebuild QEMU — Result

**Datum:** 2026-06-03  
**HEAD:** `ddd502e`  
**Gesamtstatus:** `blocked`

## Zusammenfassung

Der Fix aus `ddd502e` ist im Workspace und **teilweise** im Host-Backend (`/opt` devserver + agent) nach manuellem Sync. Die vollständige Operator-Pipeline (Deploy, `local_lab`-Repro, Clean, ISO-Rebuild, QEMU) scheiterte an **fehlendem sudo** in der Agent-Session.

| Phase | Exit / Status |
|-------|----------------|
| Deploy (official) | **1** — sudo Passwort |
| Deploy (partial /opt) | Backend-Marker **yes** |
| Local lab repro | **blocked** |
| Release before build | bereits **release** |
| Clean | **32** — root-owned |
| Prepare | **0** |
| Validate tree | **11** — stale squashfs |
| ISO build | **nicht gestartet** |
| QEMU smoke | **nicht gestartet** |

## Pflichtaussagen

- Primärblocker nach `212528` war **`agent_send_failed`**, nicht Import/Host-Header.
- Neuer Lauf muss **HTTP-Status/Response** serialisieren (`SETUPHELFER_DEVSERVER_AGENT_SEND_*`).
- **Guest-Report** entscheidet über Grün — nicht erreicht.
- **USB gesperrt.**

## Operator-Sequenz

1. `sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller`
2. `local_lab` Repro → Fleet/Dev 200 → **release** restore
3. `sudo clean-controlled-live-build-tree.sh --operator-confirm-clean`
4. prepare → validate_tree **0**
5. `scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build --profile developer-qemu`
6. `validate-rescue-iso-squashfs.sh` → **0** mit SEND-Markern im Squashfs
7. `sudo ./scripts/rescue-live/qemu-guest-agent-smoke-operator.sh`

## Evidence

Siehe `payload_fix_rebuild_qemu_latest.json` und `PAYLOAD_FIX_*` Phase-Dokumente.
