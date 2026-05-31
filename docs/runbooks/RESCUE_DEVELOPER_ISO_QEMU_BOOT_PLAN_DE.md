# Rescue Developer ISO — QEMU Boot Plan (DE)

**Version:** 1.7.3.0
**Status:** Plan only — **QEMU in diesem Dokument nicht ausführen**
**ISO-Run-ID:** `rescue_developer_iso_20260531_103047`

## Zweck

Kontrollierter QEMU-Boot-Smoke-Test der Rescue Developer Edition ISO als nächster Schritt nach erfolgreichem Controlled Build.

## Voraussetzungen (erfüllt)

| Check | Status |
|-------|--------|
| Controlled ISO Build LB_EXIT=0 | **yes** |
| ISO vorhanden | **yes** |
| SHA256 | `52da3e018ccbef827f8ad9bcccb9439c59e3131c501a21313d490f92a5c04326` |
| Developer Profile / Agent Guard | **OK** |
| Public Guard | **OK** |
| USB-Write | **nicht ausgeführt / blockiert** |

## ISO-Pfad

```
build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
```

Absolut: `/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso`

SHA256-Datei: `docs/evidence/runtime-results/rescue/rescue_developer_iso_latest.sha256`

## Host Dev Server URL (QEMU User NAT)

Im Gast ist `http://127.0.0.1:8000` der **Gast selbst**, nicht der Host.

| Kontext | URL |
|---------|-----|
| Hardware / Host lokal | `http://127.0.0.1:8000` |
| QEMU-Gast → Host (user NAT) | `http://10.0.2.2:8000` |

**Option B (wrapper default):** host `socat` proxy `0.0.0.0:8001` → `127.0.0.1:8000`; Gast-URL `http://10.0.2.2:8001`.

**Option A (Lab-Drop-in):** `scripts/rescue-live/apply-qemu-local-lab-backend-bind-dropin.sh` — siehe `docs/architecture/QEMU_HOST_DEV_SERVER_REACHABILITY_POLICY.md`.

Developer-QEMU-Profil: `build/rescue/profiles/developer-qemu/`
Agent-Resolver: `--qemu-host-fallback` / `SETUPHELFER_DEV_AGENT_QEMU_HOST_FALLBACK=true`

## Agent-Modulpfad (Rescue Runtime)

Bundle: `/opt/setuphelfer-rescue/backend/devserver_agent/cli.py`

```bash
PYTHONPATH=/opt/setuphelfer-rescue \
  python3 -m backend.devserver_agent.cli \
  --mode local_lab \
  --server http://10.0.2.2:8001 \
  --send --json
```

**Nicht:** `PYTHONPATH=/opt/setuphelfer-rescue/backend python3 -m devserver_agent.cli` (ModuleNotFoundError).

## Remote-Zugriff auf die QEMU-VM

- Lokale GTK-Konsole (`-display gtk`)
- Lokaler VNC: `-vnc 127.0.0.1:1` → `127.0.0.1:5901`
- Optional SSH-Forward: `-nic user,hostfwd=tcp:127.0.0.1:2222-:22` (nur wenn Gast-sshd aktiv)
- **Kein** `0.0.0.0`, keine LAN-/Internet-Freigabe
- QEMU-Tastatur: `-k de`
- Live: `keyboard-layouts=de`, `de_DE.UTF-8`, `Europe/Berlin`

Wrapper (Plan/Start): `scripts/rescue-live/run-qemu-developer-iso-smoke.sh`

```bash
./scripts/rescue-live/run-qemu-developer-iso-smoke.sh --dry-run
# PID: docs/evidence/runtime-results/rescue/qemu/<RUN_ID>/qemu_gtk_pid.txt (niemals /qemu_gtk_pid.txt)

qemu-system-x86_64 -m 2048 -smp 2 \
  -cdrom "$ISO_PATH" \
  -boot d -snapshot -no-reboot \
  -serial file:"docs/evidence/runtime-results/rescue/qemu/<RUN_ID>/qemu-serial.log" \
  -display gtk -k de -vnc 127.0.0.1:1 \
  -nic user,hostfwd=tcp:127.0.0.1:2222-:22 \
  -usb -device usb-tablet
```

Read-only Checks im Gast:

```bash
ps -p 1 -o comm=
localectl status || true
cat /etc/default/keyboard || true
systemctl status setuphelfer-dev-agent.service --no-pager || true
cat /etc/setuphelfer/setuphelfer-dev-agent.env || true
curl -s http://10.0.2.2:8000/api/dev-server/health || true
PYTHONPATH=/opt/setuphelfer-rescue python3 -m backend.devserver_agent.cli \
  --mode local_lab --server http://10.0.2.2:8000 --send --json || true
```

## Geplanter QEMU-Befehl (Basis, nicht ausführen in Evidence-Lauf)

```bash
ISO_PATH="/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"

qemu-system-x86_64 -m 2048 -smp 2 \
  -cdrom "$ISO_PATH" \
  -boot d -snapshot -no-reboot \
  -display gtk \
  -usb -device usb-tablet
```

## Optionales serielles Log (für späteren Smoke-Lauf)

```bash
mkdir -p docs/evidence/runtime-results/rescue

qemu-system-x86_64 -m 2048 -smp 2 \
  -cdrom "$ISO_PATH" \
  -boot d -snapshot -no-reboot \
  -serial file:docs/evidence/runtime-results/rescue/qemu-serial-latest.log \
  -display gtk \
  -usb -device usb-tablet
```

## Abnahmekriterien (späterer QEMU-Lauf)

1. ISO bootet ohne Kernel-Panic.
2. systemd ist PID 1 (`/sbin/init` → systemd).
3. Setuphelfer Rescue Runtime unter `/opt/setuphelfer-rescue` vorhanden.
4. Unit `setuphelfer-dev-agent.service` vorhanden (enabled).
5. Agent sendet nur im Modus **local_lab** an `http://127.0.0.1:8000`.
6. Kein USB-Schreiben, kein dd, keine Zielgeräte-Aktion.
7. Dev Server erhält Report, wenn Host-Netzwerk zum Gast erreichbar ist.
8. Wenn Netzwerk nicht erreichbar: Spool unter `/opt/setuphelfer-rescue/docs/evidence/runtime-results/dev-agent-spool`.

## Verboten im QEMU-Smoke-Lauf

- USB-Passthrough auf physische Sticks
- `-hda` / `-drive` auf `/dev/sd*`
- dd, mkfs, mount auf Host-Zielgeräte
- Backup/Restore/Verify Deep
- apt install/upgrade im Host

## Evidence nach QEMU-Lauf (separater Prompt)

- `docs/evidence/runtime-results/rescue/qemu-serial-latest.log`
- `docs/evidence/rescue/RESCUE_DEVELOPER_ISO_QEMU_BOOT_RESULT.md`
- Aktualisierung `rescue_developer_controlled_iso_build_result.json` → `boot.boot_test_executed=true` nur nach echtem Boot

## Referenzen

- `docs/evidence/rescue/RESCUE_DEVELOPER_CONTROLLED_ISO_BUILD_RESULT.md`
- `docs/evidence/runtime-results/rescue/rescue_developer_iso_latest.sha256`
- `docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`
