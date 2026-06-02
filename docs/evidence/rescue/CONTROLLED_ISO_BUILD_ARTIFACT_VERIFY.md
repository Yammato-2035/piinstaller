# Controlled ISO Build — Artifact Verify

**Datum:** 2026-06-02  
**Run-ID:** `rescue_developer_iso_20260602_195502`

## ISO

| Feld | Wert |
|------|------|
| ISO vorhanden | **yes** |
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | **511705088** B (~488 MiB) |
| Zeitstempel (mtime) | 2026-06-02 21:58:44 +0200 |
| SHA256 | `505989f7d348265c08e8baeaa2971f81aa855224223859ae8d536b984dafaf52` |
| file | ISO 9660 CD-ROM filesystem data (DOS/MBR boot sector) **`SETUPHELFER_RESCUE`** (bootable) |
| Owner | root:workspace 0644 |

## Neu vs. alt

| Vergleich | Ergebnis |
|-----------|----------|
| Prior archived SHA (2026-05-31) | `52da3e018ccb…` — **512 MiB** |
| Aktuelles ISO | `505989f7…` — **511705088 B** |
| Artefakt neu nach Cleanup/Build | **yes** |
| Altes ISO ausgeschlossen | **yes** (andere SHA256, andere Größe, neues mtime nach Cleanup) |

SHA256-Datei: `docs/evidence/runtime-results/rescue/controlled_iso_build_latest.sha256`

## Bewertung

**Status: ok**

Nur ein Hybrid-ISO im Build-Tree; kein stale Prior-ISO (Cleanup entfernte altes ~512-MiB-Artefakt).
