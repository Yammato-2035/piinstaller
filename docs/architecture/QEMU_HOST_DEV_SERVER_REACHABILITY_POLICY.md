# QEMU Host Dev-Server Reachability Policy

**Version:** 1.7.3.0
**Status:** Lab policy — not a production default
**Mode:** `local_lab` only — Public auto-upload remains **disabled**

## Problem

In QEMU user-NAT the guest reaches the host at `10.0.2.2`. The Setuphelfer backend on the host typically binds **`127.0.0.1:8000`** only (`scripts/start-backend.sh`, `ALLOW_REMOTE_ACCESS` default false).

Observed failure:

```text
curl -sS -m 8 http://10.0.2.2:8000/api/dev-server/health
→ curl: (28) Connection timed out after 8002 milliseconds
```

Slirp forwarding to a localhost-only listener is **not reliable** on all hosts. This is **`network_bind_pending`**, not a guest routing bug.

## Allowed options (Lab only)

### Option A — Lab backend bind (operator systemd drop-in)

**Use when:** persistent QEMU lab on one machine; operator accepts temporary wider bind.

| Rule | Value |
|------|-------|
| Mechanism | systemd drop-in sets `Environment=ALLOW_REMOTE_ACCESS=true` |
| Effect | `start-backend.sh` binds `0.0.0.0:8000` |
| Scope | **Lab only** — documented revert required |
| Public upload | **disabled** (unchanged) |
| SSH | **disabled** (unchanged) |
| Dev-server mode | `local_lab` |
| LAN/Internet | **not** a goal — firewall must block external access if host exposes `0.0.0.0` |

Example: `packaging/systemd/dropins/qemu-local-lab-bind.conf.example`
Apply: `scripts/rescue-live/apply-qemu-local-lab-backend-bind-dropin.sh --operator-confirm`

**Evidence must state:** lab bind active, not product standard.

### Option B — Host lab proxy (preferred default for smoke)

**Use when:** backend must stay on `127.0.0.1:8000`; no systemd change.

| Rule | Value |
|------|-------|
| Mechanism | `scripts/rescue-live/start-qemu-lab-dev-server-proxy.sh` — `socat` listens `0.0.0.0:8001` → `127.0.0.1:8000` |
| Guest URL | `http://10.0.2.2:8001` (QEMU user NAT to host) |
| Host listener | backend stays `127.0.0.1:8000`; proxy on `0.0.0.0:8001` |
| Scope | per QEMU smoke run (wrapper starts/stops proxy) |
| Port 8000 direct | requires Option A lab bind |

Implemented in: `scripts/rescue-live/run-qemu-developer-iso-smoke.sh` (default on).

Disable: `--no-lab-proxy`. Use Option A with `--no-lab-proxy --host-dev-server-url http://10.0.2.2:8000`.

## Forbidden

- Blind `0.0.0.0` in production/public rescue profiles
- Enabling public auto-upload
- Opening firewall to LAN/Internet without documented lab decision
- SSH enablement for ingest smoke
- Weakening safety gates

## Rescue agent module path (related)

Runtime bundle layout:

```text
/opt/setuphelfer-rescue/backend/devserver_agent/cli.py
```

Correct invocation:

```bash
PYTHONPATH=/opt/setuphelfer-rescue \
  python3 -m backend.devserver_agent.cli …
```

**Wrong** (causes `ModuleNotFoundError: devserver_agent`):

```bash
PYTHONPATH=/opt/setuphelfer-rescue/backend \
  python3 -m devserver_agent.cli …
```

systemd units in rescue ISO must use `backend.devserver_agent.cli` with `PYTHONPATH=/opt/setuphelfer-rescue`.

## Verification

1. Host: `curl -s http://127.0.0.1:8000/api/dev-server/health`
2. Guest (with Option B active): `curl -sS -m 8 http://10.0.2.2:8000/api/dev-server/health`
3. Agent: `python3 -m backend.devserver_agent.cli --send --json` with env above
4. Host: `GET /api/dev-server/summary` — new node/report or documented spool

## References

- `docs/runbooks/RESCUE_DEVELOPER_ISO_QEMU_BOOT_PLAN_DE.md`
- `docs/evidence/rescue/RESCUE_QEMU_HOST_REACHABILITY_AND_AGENT_MODULE_PATH_FIX.md`
- `build/rescue/profiles/developer-qemu/`
