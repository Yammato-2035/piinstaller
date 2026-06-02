# Controlled ISO Build — Boot Menu / Branding Review

**Datum:** 2026-06-02

## Build-Tree (binary/isolinux)

| Datei | Größe | Hinweis |
|-------|-------|---------|
| splash.png | 49093 B | Setuphelfer-Branding |
| bootlogo | 2048 B | vorhanden |
| live.cfg | 770 B | systemd init + setuphelfer_rescue |
| isolinux.bin, *.c32 | vorhanden | Syslinux-Stack |

## ISO-Inhalt

`/isolinux/splash.png`, `menu.cfg`, `live.cfg` auf ISO bestätigt (isoinfo).

## cp-Wildcard-Warnungen

Betreffen **optionale** Syslinux-Dateien (`*.fnt`, `*.hlp`, `*.jpg`, `*.pcx`, `*.tr`, `langlist`) — **nicht** splash.png oder live.cfg. rsvg-Mitigation wirksam (splash.png erzeugt, LB binary stage OK).

## Bewertung

**Status: ok**

Branding und Bootmenü-Konfiguration vorhanden; Wildcard-cp-Warnungen nicht fatal.
