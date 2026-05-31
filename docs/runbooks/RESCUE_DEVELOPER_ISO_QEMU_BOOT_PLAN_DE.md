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

## Geplanter QEMU-Befehl (nicht ausführen in Evidence-Lauf)

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
