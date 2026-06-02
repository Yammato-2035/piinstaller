# Developer-QEMU ISO After Autopilot — Serial / Bootappend Fingerprint

**Datum:** 2026-06-03  
**Log:** `docs/evidence/rescue/developer_qemu_iso_after_autopilot_serial_fingerprint_latest.log`

## Pflichtbewertung

| Kriterium | Ergebnis | Beleg |
|-----------|----------|-------|
| console=ttyS0 belegt | **yes** | `config/binary`, `binary/isolinux/live.cfg` |
| console=tty0 belegt | **yes** | gleiche Bootappend-Zeilen |
| SERIAL 0 115200 belegt | **yes** | `config/bootloaders/isolinux/isolinux.cfg`, `binary/isolinux/isolinux.cfg` |
| init=/lib/systemd/systemd belegt | **yes** | Bootappend in `live.cfg` / `config/binary` |
| quiet/splash im Developer-QEMU-Profil nicht aktiv | **yes** | Kein `quiet splash` in developer-qemu Bootappend (nur `nosplash` in Memtest-Eintrag) |
| Devserver-Endpunkt belegt | **yes** | `http://10.0.2.2:8001` in Autopilot-Unit und `setuphelfer-dev-agent.env` |

**Status:** `ok`
