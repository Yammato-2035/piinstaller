# Rescue ISO — systemd Init Rebuild Result

**Klassifikation:** `systemd_rebuild_prepared_not_executed`

Fix im Build-Tree (`init=/lib/systemd/systemd`, `dbus`). **Kein** `lb build` — `RESCUE_SYSTEMD_REBUILD_FREIGEGEBEN` nicht gesetzt.

Alte ISO: Validator Exit **15** (fehlendes `init=` in `live.cfg`).

## Operator-Rebuild

```bash
export RESCUE_SYSTEMD_REBUILD_FREIGEGEBEN=1
cd /home/volker/piinstaller
# clean + prepare + run-controlled-iso-build-with-logging.sh --operator-confirm-build
./scripts/rescue-live/validate-rescue-iso-squashfs.sh \
  build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
# Ziel: Exit 0 inkl. systemd init
```

Danach VM: `ps -p 1 -o comm=` → `systemd`, dann `systemctl status setuphelfer-backend.service`.

JSON: `rescue_iso_systemd_init_rebuild_result_latest.json`
