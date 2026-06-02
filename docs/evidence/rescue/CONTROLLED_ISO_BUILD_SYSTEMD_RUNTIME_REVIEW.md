# Controlled ISO Build — systemd / Runtime Integration Review

**Datum:** 2026-06-02

## Bootappend / Init

| Prüfpunkt | Ergebnis |
|-----------|----------|
| `init=/lib/systemd/systemd` in auto/config | **yes** |
| `init=/lib/systemd/systemd` in isolinux live.cfg (ISO) | **yes** |
| dbus in Squashfs | **yes** (Validator Exit 0) |

## Services im Squashfs

| Unit | Datei | multi-user.target.wants |
|------|-------|-------------------------|
| setuphelfer-backend.service | yes | **yes** |
| setuphelfer.service | yes | **yes** |
| setuphelfer-dev-agent.service | yes | **no** (oneshot; manuell/profilgesteuert) |

## Dev-Agent-Unit (Squashfs)

```
Environment=PYTHONPATH=/opt/setuphelfer-rescue
ExecStart=/usr/bin/python3 -m backend.devserver_agent.cli --send --json --qemu-host-fallback
```

Extrakt: `controlled_iso_build_dev_agent_unit_latest.txt` (gitignored).

## Bewertung

**Status: ok**

Backend/UI enabled; Dev-Agent vorhanden mit geprüftem PYTHONPATH. Kein Fake-Grün für Rescue-Agent-E2EE (Contract-Stubs nicht im Bundle).
