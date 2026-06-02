# Developer-QEMU ISO After Autopilot — Squashfs Review

**Datum:** 2026-06-03  
**Squashfs:** `build/rescue/live-build/setuphelfer-rescue-live/binary/live/filesystem.squashfs`  
**Validator-Log:** `docs/evidence/rescue/developer_qemu_iso_after_autopilot_squashfs_validator_latest.log`

## Pflichtbewertung

| Kriterium | Ergebnis |
|-----------|----------|
| Squashfs vorhanden | **yes** |
| setuphelfer runtime bundle vorhanden | **yes** (`opt/setuphelfer-rescue/MANIFEST.json`) |
| devserver_agent vorhanden | **yes** (`setuphelfer-dev-agent.service`, env `10.0.2.2:8001`) |
| rescue_agent vorhanden | **no** (Modul nicht im Squashfs-Bundle) |
| rescue_agent erforderlich | **no** |
| Autopilot-Service vorhanden | **yes** |
| Autopilot-Wants im Squashfs vorhanden | **yes** |
| Autopilot-Wants Ziel plausibel | **yes** (`multi-user.target.wants/setuphelfer-qemu-smoke-autopilot.service → ../setuphelfer-qemu-smoke-autopilot.service`) |
| Dev-Agent-Service vorhanden | **yes** |
| Dev-Agent enabled/wanted | **no** (Unit vorhanden, nicht in wants — Autopilot startet Agent) |
| Devserver-Endpunkt 10.0.2.2:8001 vorhanden | **yes** |
| Squashfs-Validator Exit | **0** |

Validator-Ausgabe:

```
OK: developer-qemu autopilot unit enabled in squashfs
OK: rescue ISO squashfs — bundle, systemd init, enabled units, de keyboard/locale, login hints, developer-qemu autopilot
```

**Status:** `ok`
