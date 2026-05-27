# Rescue ISO — isohybrid Failure (RESCUE-BUILD-ISOHYBRID-001)

**Datum:** 2026-05-27 · **HEAD:** `bdfbb41`

## Symptom

```text
231515 extents written (452 MB)
binary.sh: 5: isohybrid: not found
LB_EXIT=127
```

## Einordnung

| Feld | Wert |
|------|------|
| Klassifikation | `build_failed` |
| Policy/TTY | OK — echter Operator-Build |
| rsvg/bootlogo | überwunden |
| `isohybrid` | **fehlt im Chroot** während `binary.sh` |

`genisoimage` erzeugt `binary.hybrid.iso` (~452 MB) unter `chroot/`. Der anschließende **`isohybrid`**-Schritt scheitert — die ISO ist **nicht** als belastbares Hybrid-Artefakt freigegeben.

## Ursache

`lb_binary_iso` installiert für `iso-hybrid` standardmäßig das Debian-Paket **`syslinux`**. **`isohybrid`** liegt auf Bookworm in **`syslinux-utils`**, nicht in `syslinux`.

Host kann `isohybrid` haben — irrelevant, weil `binary.sh` **im Chroot** läuft (`Chroot chroot "sh binary.sh"`).

## Fix (minimal, ohne apt im Cursor-Lauf)

1. `config/package-lists/setuphelfer.list.binary` mit **`syslinux-utils`**
2. Preflight im Wrapper: Paketliste + Host-Hinweis
3. Operator: `prepare-controlled-live-build-tree.sh`, `./auto/clean`, Build-Retry

JSON: `rescue_iso_isohybrid_failure_latest.json`
