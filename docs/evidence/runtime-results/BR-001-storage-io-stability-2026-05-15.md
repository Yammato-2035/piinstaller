# BR-001 Storage / I-O Stability (2026-05-15)

## Ergebnis

**Analyse abgeschlossen (gelb):** Root Cause = USB-Disconnect am Hub `usb 1-2.1` unter Schreiblast. **15 GiB-Stabilitätstest** auf neu gemountetem `setuphelfer-back1` **bestanden**. Full-Retry noch nicht gestartet.

## Kompressor

- **gzip** (`tar -czf`) — **kein pigz** (`pigz` nicht im PATH)
- Keine parallele Kompression; 1 Thread

## Stabilitätstest

| | |
|--|--|
| Größe | 15 GiB |
| Dauer | 139 s (~110 MiB/s) |
| dd exit | 0 |
| Disconnect | nein |

Details: `docs/knowledge-base/storage/BR-001-external-hdd-usb-stability.md`
