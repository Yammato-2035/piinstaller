# Controlled ISO Build — Log Review

**Datum:** 2026-06-02  
**Log:** `build/rescue/logs/controlled-iso-build/latest.log` (~741 KiB)

## Kernergebnis

| Prüfpunkt | Ergebnis |
|-----------|----------|
| LB_EXIT=0 im Log | **yes** |
| cp binary/isolinux wildcard warnings | **yes** (6 Zeilen) |
| Warnungen fatal | **no** |
| apt install/remove im Build-Kontext | **yes** (live-build-intern: memtest86+, syslinux, librsvg2-bin, genisoimage; danach genisoimage/syslinux remove) |
| Keine USB/dd/Restore-Aktion | **yes** |

## cp isolinux Wildcard-Warnungen

```
cp: Aufruf von stat für 'binary/isolinux/*.fnt' nicht möglich
cp: … *.hlp, *.jpg, *.pcx, *.tr, langlist
```

Optionale Syslinux-Hilfsdateien fehlen im Binary-Stage; Build setzte fort, ISO und splash.png erzeugt.

## Weitere nicht-fatale Hinweise

- `Warning: creating filesystem that does not conform to ISO-9660` (Hybrid-Boot, erwartbar)
- `update-rc.d` / `insserv` Warnungen im Chroot (Debian live-build üblich)
- `apt-key is deprecated` (live-build Chroot)

## Bewertung

**Status: ok**

Kein Build-Abbruch, LB_EXIT=0, Hybrid-ISO geschrieben (249402 extents / 487 MB).
