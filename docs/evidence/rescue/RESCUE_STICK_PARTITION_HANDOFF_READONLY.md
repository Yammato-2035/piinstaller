# Rettungsstick – Partitions-Handoff (read-only Evidence)

**Datum:** 2026-05-22
**Modus:** Nur Dokumentation und API-Vorschau – **kein** Build, **kein** Device-Write.

## Vorbereitet

- Architektur: `docs/architecture/RESCUE_STICK_PARTITION_HANDOFF.md`
- API liefert `rescue_handoff_next` in Restore-Handoff-Preview
- Partitions-UI zeigt Handoff + Gates ohne Schreibbuttons

## Explizit nicht ausgeführt

ISO-Erzeugung, `lb build`, debootstrap, chroot, `apt install`, `dd`, Stick-Partitionierung, Bootloader-Write.

## Nächster Schritt (Operator)

1. Partitions-Finalisierung in Runtime deployen und Gate 0 prüfen
2. Rettungsstick-Spezifikation (Live-OS) freigeben
3. Erst dann: read-only Stick-Inspect + Handoff-Validierung am echten Medium
