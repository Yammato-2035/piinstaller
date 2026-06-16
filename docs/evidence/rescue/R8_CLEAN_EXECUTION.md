# R.8 — Clean Execution

**Datum:** 2026-06-13

## Befehl

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
```

## Ergebnis

| Feld | Wert |
|------|------|
| Ausgeführt | **nein** |
| Exit | **1** |
| Grund | `sudo: Ein Passwort ist notwendig` (kein TTY / kein passwordless sudo) |

## Post-Clean Prüfung (unverändert)

```bash
find build/rescue/live-build/setuphelfer-rescue-live -user root | wc -l
```

| Feld | Wert |
|------|------|
| root-owned Einträge | **64561** (weiterhin blockiert) |

Sample (maxdepth 3):

```
build/rescue/live-build/setuphelfer-rescue-live/chroot
build/rescue/live-build/setuphelfer-rescue-live/chroot/usr
build/rescue/live-build/setuphelfer-rescue-live/.build/...
build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
```

## Entscheidung

**STOP** — Clean nicht abgeschlossen. Kein ISO-Build starten (LB_EXIT=34 erwartet).

## Operator-Aktion erforderlich

Im **interaktiven Operator-Terminal**:

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
find build/rescue/live-build/setuphelfer-rescue-live -user root | wc -l
# Erwartung: 0 oder nur vernachlässigbare Reste
```
