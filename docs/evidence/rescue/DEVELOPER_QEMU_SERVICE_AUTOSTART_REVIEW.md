# Developer QEMU Service Autostart Review (Phase 2)

**Datum:** 2026-06-02  
**Logs:** `developer_qemu_service_occurrences_latest.log`, `developer_qemu_service_contents_latest.log`

## Checkliste

| Prüfpunkt | Ergebnis |
|-----------|----------|
| `setuphelfer-dev-agent.service` vorhanden | yes (developer-Profil; im developer-qemu-Tree via Bundle, **nicht** separat enabled) |
| `setuphelfer-qemu-smoke-autopilot.service` vorhanden | yes |
| Beide services enabled/wanted (Prepare-only) | **Nein** — Enable erfolgt im Chroot via Hook 090 beim ISO-Build |
| Profiltyp für Enable | **developer-qemu only** (Hook 090) |
| Darf in Standard-ISO aktiv sein? | **Nein** — Standard-Profil hat weder Hook 090 noch Serial-Bootappend |

## Hook 090 (developer-qemu)

```sh
systemctl enable setuphelfer-serial-boot-markers.service
systemctl enable setuphelfer-qemu-smoke-autopilot.service
```

## Autopilot-Service (Auszug)

- `SETUPHELFER_DEV_AGENT_SERVER_URL=http://10.0.2.2:8001`
- `WantedBy=multi-user.target`
- `TTYPath=/dev/ttyS0`

## Empfehlung

**developer-qemu-only enable** — Autopilot + Serial-Marker nur im Developer-QEMU-Profil. Standard-Release-ISO bleibt defensiv (`quiet splash`, keine Dev-Callbacks).

`write_dev_agent_enable_hook false` bei developer-qemu: separater dev-agent-Enable bewusst aus — Autopilot ruft `devserver_agent.cli` direkt auf.

## Status

**ok** (Design korrekt; Runtime-Enable erst nach ISO-Rebuild mit developer-qemu-Profil nachweisbar via `validate-rescue-iso-squashfs.sh`)
