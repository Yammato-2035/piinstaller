# Rescue QEMU Host Reachability and Agent Module Path Fix

**Date:** 2026-05-31
**HEAD Start:** 894b726
**Branch:** main
**Version:** 1.7.3.0

## Ausgangsfehler

| Fehler | Symptom |
|--------|---------|
| Host reachability | `curl http://10.0.2.2:8000/api/dev-server/health` → timeout (28) |
| Agent module path | `python3 -m devserver_agent.cli` → `ModuleNotFoundError: devserver_agent` |

## Ursachen

1. **Backend bind:** `127.0.0.1:8000` only — Slirp von `10.0.2.2:8000` timeout.
2. **Falscher Modulpfad:** ISO/prepare nutzte `PYTHONPATH=/opt/setuphelfer-rescue/backend` + `-m devserver_agent.cli`. Korrekt: `PYTHONPATH=/opt/setuphelfer-rescue` + `-m backend.devserver_agent.cli`.
3. **QEMU guestfwd:** in QEMU 8.2 keine gültige Regel für `10.0.2.2:8000-cmd:socat…` — verworfen.

## Fix

### Host reachability (Option B — Lab-Proxy, Standard)

| Komponente | Änderung |
|------------|----------|
| `start-qemu-lab-dev-server-proxy.sh` | `socat 0.0.0.0:8001` → `127.0.0.1:8000` |
| `run-qemu-developer-iso-smoke.sh` | startet/stoppt Proxy; Gast-URL `http://10.0.2.2:8001` |
| Policy | `docs/architecture/QEMU_HOST_DEV_SERVER_REACHABILITY_POLICY.md` |

**Option A (optional):** `apply-qemu-local-lab-backend-bind-dropin.sh` — `ALLOW_REMOTE_ACCESS=true` für direktes `10.0.2.2:8000` (root, Lab only).

### Agent module path

| Datei | Fix |
|-------|-----|
| `prepare-controlled-live-build-tree.sh` | `backend.devserver_agent.cli`, `PYTHONPATH=/opt/setuphelfer-rescue`, Profil `developer-qemu` |
| `build/rescue/profiles/developer-qemu/systemd/` | Rescue-Pfade + korrektes Modul |
| Runbooks DE/EN | Beispiele mit `backend.devserver_agent.cli` |

### developer-qemu Profil

- Server-URL: `http://10.0.2.2:8001` (Option B Proxy)
- Build-Tree `includes.chroot` verifiziert: `ExecStart=… backend.devserver_agent.cli --qemu-host-fallback`

## Tests

| Suite | Ergebnis |
|-------|----------|
| `test_devserver_agent_rescue_runtime_module_path_v1.py` | **8 OK** |
| `test_devserver_agent_*` gesamt | **88 OK** |
| Profile guard | **exit 0** |

## Neue ISO

| Feld | Wert |
|------|------|
| Gebaut | **nein** — preflight `blocked` (`root_owned_active_work_areas`, sudo clean erforderlich) |
| Prepare-Tree | **ja** — `developer-qemu` mit korrektem systemd/env in `includes.chroot` |
| Alte ISO SHA | `52da3e018ccb…` (noch im Squashfs: falscher Modulpfad) |

## QEMU-Smoke (dieser Lauf)

| Check | Ergebnis |
|-------|----------|
| Lab-Proxy lokal | **OK** — `curl 127.0.0.1:8001/api/dev-server/health` |
| QEMU gestartet | Wrapper getestet; voller Gast-Ingest **pending** (neue ISO + Operator) |
| Host-Report neu | **nein** (kein abgeschlossener Gast-Send-Lauf) |
| Keyboard | manuell `setxkbmap de` (unverändert) |

**Status:** `review_required` — Fixes im Repo/Prepare-Tree; Ingest-Erfolg nach ISO-Rebuild + QEMU-Lauf mit Proxy.

## Safety

USB/dd/Backup/Restore/apt: **false**. Public auto-upload: **disabled**. SSH: **disabled**. Proxy bind `0.0.0.0:8001` nur Lab, kein Produktstandard.

## Nächster Schritt

1. `sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean`
2. ISO-Build `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu`
3. QEMU-Smoke mit Wrapper (Proxy auto) + `backend.devserver_agent.cli --send`
4. Bei Erfolg: Release-Gate / Regression-Runbook

## Evidence

- Policy: `docs/architecture/QEMU_HOST_DEV_SERVER_REACHABILITY_POLICY.md`
- Vorheriger Ingest: `RESCUE_DEVELOPER_ISO_QEMU_HOST_INGEST_RESULT.md`
