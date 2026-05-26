# Rescue ISO rsvg Failure Analysis

**Datum:** 2026-05-26
**Git HEAD vor Fix-Commit:** `3adfc13`
**Status:** `PREBUILD_HARDENED_PENDING_REBUILD`

## Exakter Fehler

Der letzte echte Operator-Build endete mit:

```text
/usr/bin/env: 'rsvg': No such file or directory
LB_EXIT=127
```

## Build-Phase

Der Aufruf kommt aus der `live-build`-Phase:

- `/usr/lib/live/build/lb_binary_syslinux`

Diese Phase erzeugt fuer das Syslinux/Isolinux-Bootmenue aus:

- `config/bootloaders/isolinux/splash.svg.in`

eine temporaere `splash.svg` und ruft anschliessend `rsvg --format png --height 480 --width 640 ...` fuer `splash.png` auf.

## Belastbare Ursache

Belastbare Befunde aus dem aktuellen Stand:

- im kontrollierten Build-Tree liegt `config/bootloaders/isolinux/splash.svg.in`
- `/usr/lib/live/build/lb_binary_syslinux` enthaelt sowohl den expliziten `rsvg`-Aufruf als auch den Paket-Hinweis `librsvg2-bin`
- `command -v rsvg` -> **kein Treffer**
- `command -v rsvg-convert` -> **kein Treffer**
- `LB_BUILD_WITH_CHROOT` ist in `/usr/share/live/build/functions/defaults.sh` standardmaessig auf `true` gesetzt; der Build-Tree ueberschreibt das nicht

Damit ist der Fehler eindeutig ein `live-build`-Bootloader-/Binary-Stage-Thema und **keine** Rescue-Live-Image-Runtime-Abhaengigkeit des finalen Systems.

## rsvg oder rsvg-convert?

Der aktuelle `live-build`-Schritt erwartet den Legacy-Befehl:

- `rsvg`

Geprueft wurde:

- `rsvg` fehlt
- `rsvg-convert` fehlt ebenfalls

Damit ist fuer den aktuellen Host bereits vor dem Build sichtbar, dass die benoetigte Build-Abhaengigkeit fehlt.

## Minimaler Fix

Umgesetzt wurde **kein** Paketinstallations-Schritt, sondern eine minimale Vorab-Haertung:

1. Dashboard/Executor erkennen jetzt die fehlende RSVG-Build-Abhaengigkeit **vor** `lb build`.
2. Der Status wird als `blocked_build_tools_missing` eingeordnet.
3. `next_operator_action` nennt nur den Operator-Hinweis:

```bash
sudo apt install librsvg2-bin
```

4. Der Build bleibt blockiert, bis diese Abhaengigkeit verfuegbar ist.

## Warum dieser Fix minimal und korrekt ist

- kein `apt install` in diesem Lauf
- kein `lb build` in diesem Lauf
- keine Aenderung an USB-/Write-Gates
- kein spekulativer Wechsel der Paketliste im Live-Image
- die reale Failure-Ursache wird jetzt frueh sichtbar, statt erst spaet mit `LB_EXIT=127`

## Einordnung der Abhaengigkeit

- **Typ:** Build-Abhaengigkeit der `live-build`-Toolchain
- **Nicht:** Laufzeitabhaengigkeit der spaeteren Rescue-ISO
- **Paket-Hinweis aus `live-build`:** `librsvg2-bin`

## Naechster erlaubter Operator-Schritt

- Build-Abhaengigkeit bereitstellen oder Build-Host entsprechend vorbereiten
- danach Dashboard-Preflight erneut pruefen
- **kein** ISO-Build in diesem Analyse-/Fix-Lauf
