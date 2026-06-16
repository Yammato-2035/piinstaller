# R.5 — Controlled ISO Build Log

## Status

**Nicht ausgeführt** — Gate A fehlt (`OPERATOR_ISO_BUILD_FREIGABE=0`).

## Geplanter Build-Pfad

```text
scripts/rescue-live/run-controlled-iso-build-with-logging.sh
```

Vor Build empfohlen:

```bash
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh
./scripts/rescue-live/validate-live-build-dpkg-preflight.sh
export OPERATOR_ISO_BUILD_FREIGABE=1
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh
```

## Vorhandene ISO (stale, nur Referenz)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 652M (683671552 B) |
| Datum | 2026-06-07 16:23 |
| SHA256 | `c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194` |
| R.4-Stack | **nein** — Build vor Kiosk/Browser-Package-Liste |

## Klassifikation

`blocked_iso_build_not_run` — kein Fehler, Operator-Gate ausstehend.
