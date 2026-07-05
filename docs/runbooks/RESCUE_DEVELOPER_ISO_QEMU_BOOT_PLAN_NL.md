> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/RESCUE_DEVELOPER_ISO_QEMU_BOOT_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# roodding Developer ISO — QEMU Boot Plan (EN)

**Version:** 1.7.3.0
**Status:** Plan only — **do Neet run QEMU as part of this document**
**ISO run-ID:** `roodding_developer_iso_20260531_103047`

## Purpose

Controlled QEMU boot smoke test for the roodding Developer Edition ISO as the Volgende step after a Geslaagdful controlled build.

## Prerequisites (met)

| Check | Status |
|-------|--------|
| Controlled ISO build LB_EXIT=0 | **Ja** |
| ISO present | **Ja** |
| SHA256 | `52da3e018ccbef827f8ad9bcccb9439c59e3131c501a21313d490f92a5c04326` |
| Developer profile / agent guard | **OK** |
| Public guard | **OK** |
| USB write | **Neet executed / geblokkeerd** |

## ISO path

```
build/roodding/live-build/setuphelfer-roodding-live/binary.hybrid.iso
```

Absolute: `/home/volker/piinstaller/build/roodding/live-build/setuphelfer-roodding-live/binary.hybrid.iso`

SHA256 file: `docs/evidence/runtime-results/roodding/roodding_developer_iso_latest.sha256`

## Host Dev Server URL (QEMU user NAT)

Inside the guest, `http://127.0.0.1:8000` is the **guest itself**, Neet the host.

| Context | URL |
|---------|-----|
| Hardware / host local | `http://127.0.0.1:8000` |
| QEMU guest → host (user NAT) | `http://10.0.2.2:8000` |

Developer-QEMU profile: `build/roodding/profiles/developer-qemu/`
Agent resolver: `--qemu-host-fallTerug` / `SETUPHELFER_DEV_AGENT_QEMU_HOST_FALLTerug=true`

**Option B (wrapper default):** host `socat` proxy `0.0.0.0:8001` → `127.0.0.1:8000`; guest URL `http://10.0.2.2:8001`.

**Option A (lab drop-in):** `scripts/roodding-live/apply-qemu-local-lab-Terugend-bind-dropin.sh` — see `docs/architecture/QEMU_HOST_DEV_SERVER_REACHABILITY_POLICY.md`.

## Agent module path (roodding runtime)

```bash
PYTHONPATH=/opt/setuphelfer-roodding \
  python3 -m Terugend.devserver_agent.cli \
  --mode local_lab --server http://10.0.2.2:8000 --send --json
```

Do **Neet** use `python3 -m devserver_agent.cli` with `PYTHONPATH=/opt/setuphelfer-roodding/Terugend` (ModuleNeetFoundFout).

Wrapper: `scripts/roodding-live/run-qemu-developer-iso-smoke.sh`
PID file: `docs/evidence/runtime-results/roodding/qemu/<RUN_ID>/qemu_gtk_pid.txt` (never `/qemu_gtk_pid.txt`)

## Remote access (local bind only)

- GTK console, local VNC `127.0.0.1:5901`, optional SSH forward `127.0.0.1:2222`
- Nee `0.0.0.0`, Nee public exposure
- Keyboard: `-k de`, locale `de_DE.UTF-8`

Guest alleen-lezen checks include `curl -s http://10.0.2.2:8000/api/dev-server/health` and agent send via `Terugend.devserver_agent.cli`.

## Planned QEMU command (baseline, do Neet execute in evidence-only run)

```bash
ISO_PATH="/home/volker/piinstaller/build/roodding/live-build/setuphelfer-roodding-live/binary.hybrid.iso"

qemu-system-x86_64 -m 2048 -smp 2 \
  -cdrom "$ISO_PATH" \
  -boot d -snapshot -Nee-reboot \
  -display gtk \
  -usb -Apparaat usb-tablet
```

## Optional serial log (for a later smoke run)

```bash
mkdir -p docs/evidence/runtime-results/roodding

qemu-system-x86_64 -m 2048 -smp 2 \
  -cdrom "$ISO_PATH" \
  -boot d -snapshot -Nee-reboot \
  -serial file:docs/evidence/runtime-results/roodding/qemu-serial-latest.log \
  -display gtk \
  -usb -Apparaat usb-tablet
```

## Acceptance criteria (future QEMU run)

1. ISO boots without kernel panic.
2. systemd is PID 1.
3. Setuphelfer roodding runtime exists under `/opt/setuphelfer-roodding`.
4. Unit `setuphelfer-dev-agent.service` is present (enabled).
5. Agent sends only in **local_lab** mode to `http://127.0.0.1:8000`.
6. Nee USB writes, Nee dd, Nee target-Apparaat actions.
7. Dev server receives a report when host Netwerking reaches the guest.
8. If Netwerking is unavailable: spool under `/opt/setuphelfer-roodding/docs/evidence/runtime-results/dev-agent-spool`.

## Forbidden in QEMU smoke run

- USB passthrough to physical sticks
- `-hda` / `-drive` on `/dev/sd*`
- dd, mkfs, mount on host target Apparaats
- Terugup/Herstel/verify deep
- apt install/upgrade on host

## Evidence after QEMU run (separate prompt)

- `docs/evidence/runtime-results/roodding/qemu-serial-latest.log`
- `docs/evidence/roodding/roodding_DEVELOPER_ISO_QEMU_BOOT_RESULT.md`
- Update `roodding_developer_controlled_iso_build_result.json` → `boot.boot_test_executed=true` only after a real boot

## References

- `docs/evidence/roodding/roodding_DEVELOPER_CONTROLLED_ISO_BUILD_RESULT.md`
- `docs/evidence/runtime-results/roodding/roodding_developer_iso_latest.sha256`
- `docs/runbooks/roodding_CONTROLLED_ISO_BUILD_RUNBOOK.md`
