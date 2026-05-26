# Rescue USB Write Result

**Datum:** 2026-05-25
**Git HEAD:** `fe36af0`
**Status:** `USB_WRITE_ABORTED_BUILD_FAILED`

## Ausgangslage

Der Strict-Mode-Lauf erlaubte USB-Schreiben nur nach:

- erfolgreichem ISO-Build
- vorhandener ISO mit SHA256
- erfolgreichem Systemdisk-Schutz
- doppelter exakter Operator-Bestaetigung

## Ergebnis

Diese Bedingungen wurden **nicht** erreicht.

| Feld | Wert |
|------|------|
| `LB_EXIT` | **127** |
| ISO vorhanden | **nein** |
| ISO-Pfad | `null` |
| ISO-SHA256 | `null` |
| USB-Zielgeraet | `null` |
| Bestaetigung 1 | **nicht erfolgt** |
| Bestaetigung 2 | **nicht erfolgt** |
| `dd` ausgefuehrt | **nein** |
| USB-Verify ausgefuehrt | **nein** |

## Blocker

- echter Build-Fehler: `/usr/bin/env: 'rsvg': No such file or directory`
- `LB_EXIT=127`
- keine `.iso` erzeugt
- nach dem Root-Build root-owned/stale Build-State, daher `sudo_clean_required`

## Bewertung

Der USB-Write-Gate blieb korrekt geschlossen. Es wurde bewusst:

- kein Zielgeraet gewaehlt
- keine Systemdisk-Pruefung fuer ein konkretes Zielgeraet fortgesetzt
- keine Operator-Bestaetigung angenommen
- kein `dd` ausgefuehrt

## Notification-Follow-up

Der geblockte USB-Folgepfad bleibt Teil des Rescue-Failure-Kontexts:

- `usb_write_started = false`
- `usb_target = null`
- `operator_confirm_1 = false`
- `operator_confirm_2 = false`
- `dd_executed = false`
- `usb_verify_executed = false`

Diese Fakten werden im Rescue-Notification-Event referenziert; die produktive Runtime-Abnahme des Notification-Panels ist inzwischen erfolgt:

- `GET /api/dev-dashboard/notifications/status` -> `200`
- `GET /api/dev-dashboard/notifications/events` -> `200`
- produktive Persistenzpfade: `/var/lib/setuphelfer/notifications/notification_events.jsonl` und `/var/lib/setuphelfer/notifications/notification_latest_summary.json`

Der Dashboard-Pfad ist damit fuer den geblockten USB-Folgekontext produktiv verifiziert. Der produktive E-Mail-Versand bleibt aktuell gelb, weil der SMTP-Provider echte Sendungen derzeit mit `554 5.7.0 ... limit on the number of allowed outgoing messages was exceeded` ablehnt.

## Verbotene Aktionen weiterhin nicht ausgefuehrt

- kein USB-Write
- kein `dd`
- kein `mkfs`
- kein `parted write`
- kein Restore
- kein Backup
- kein Verify Deep
