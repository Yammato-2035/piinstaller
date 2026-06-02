# Controlled ISO Build — Post-Build Cleanup Review

**Datum:** 2026-06-02

## Mounts

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Aktive Mounts unter BUILD_TREE | **none** |
| Globale Mounts (chroot/live-build) | **none** |

## Root-owned

| Prüfpunkt | Ergebnis |
|-----------|----------|
| root-owned Pfade nach Build | **44377** (chroot + binary-Artefakte, erwartet nach `lb build`) |
| ISO owner | root:workspace |
| Bewertung | **expected** — kein Mount-Leak; chroot bleibt root-owned bis nächster Clean |

## Artefakte

| Datei | Größe | mtime |
|-------|-------|-------|
| binary.hybrid.iso | 511705088 | 2026-06-02 21:58:44 |
| binary/live/filesystem.squashfs | 433651712 | 2026-06-02 21:58:15 |
| binary/live/initrd.img | 35665226 | 2026-06-02 21:58:26 |

Kein zweites/stale ISO im Tree.

## Bewertung

**Status: ok**

Neues ISO eindeutig; keine aktiven Mounts; root-owned chroot ist live-build-Normalzustand, kein Cleanup-Blocker für QEMU-Smoke.
