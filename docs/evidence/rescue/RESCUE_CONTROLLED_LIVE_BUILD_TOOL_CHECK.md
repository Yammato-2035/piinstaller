# Rescue Controlled Live Build — Tool Check

**Datum:** 2026-05-24
**Git HEAD:** `0d211fc`
**Phase:** Read-only Prüfung (kein apt install)

## Ergebnis

**Status:** `blocked_build_tools_missing` für ISO-Build — Build-Tree-Vorbereitung trotzdem möglich.

| Tool | vorhanden | Pfad | Bemerkung |
|------|-----------|------|-----------|
| lb | **nein** | — | Paket `live-build` — erforderlich für `lb config` / `lb build` |
| xorriso | **nein** | — | ISO-Erzeugung; oft via `live-build`/`genisoimage`-Abhängigkeit |
| grub-mkrescue | **ja** | `/usr/bin/grub-mkrescue` | Bootloader-Hybrid-ISO |
| mksquashfs | **ja** | `/usr/bin/mksquashfs` | Squashfs für Live-Root |
| sha256sum | **ja** | `/usr/bin/sha256sum` | Manifest/ISO-Prüfsummen |
| tar | **ja** | `/usr/bin/tar` | Bundle-Transport |
| rsync | **ja** | `/usr/bin/rsync` | Build-Tree + Bundle-Kopie |

## Bewertung

| Kriterium | Status |
|-----------|--------|
| Build-Tree vorbereiten | **erlaubt** |
| `lb build` ausführen | **blockiert** — `lb` fehlt |
| ISO-Build-Prep READY | **nein** — Tools fehlen → **ISO_BUILD_PREP_REVIEW_REQUIRED** |

## Operator vor ISO-Build

1. Phase 0 Runtime-Gate
2. `live-build` (+ Abhängigkeiten inkl. xorriso) auf Build-Host installieren — **separater Operator-Schritt**, nicht in Repo-Agent
3. Toolcheck wiederholen
4. Explizite Operator-Freigabe gemäß `RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`

**real_iso_build_allowed:** `false`
**usb_write_allowed:** `false`
