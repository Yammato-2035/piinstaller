# Developer ISO — Bootloader Serial Capture Static Validation

**Stand:** 2026-06-01
**HEAD:** `ede7784`
**ISO-SHA (aktuell, unverändert):** `be016f2adacfc9906b4b92ca8ab0d6b0390ad1e39a1e2cbb1f0a98eb35241a3f`
**Build ausgeführt:** no (Prepare-only + blockierter Build-Versuch)

## Tree-Befund (developer-qemu, nach Prepare)

| Kriterium | Ergebnis |
|-----------|----------|
| ISOLINUX `SERIAL 0 115200` | **yes** |
| `CONSOLE 0` / `PROMPT 0` | **yes** |
| `TIMEOUT 30` | **yes** |
| `DEFAULT live-` / `ONTIMEOUT live-` | **yes** |
| GRUB Serial vorgesehen | **yes** (binary hook) |
| `console=tty0` | **yes** |
| `console=ttyS0,115200n8` | **yes** |
| `quiet`/`splash` Developer-Bootpfad aktiv | **no** |
| Marker (Autopilot/Agent) im Tree | **no** (Profil-Quelle: `build/rescue/profiles/developer-qemu/`) |

## ISO-`strings`-Befund (bestehende ISO, Pre-`2e0216f`-Rebuild)

| Kriterium | ISO |
|-----------|-----|
| `console=tty0` | **yes** |
| `console=ttyS0` | **yes** |
| ISOLINUX `SERIAL 0 115200` | **no** |
| `TIMEOUT 30` | **no** |
| `DEFAULT live-` / `ONTIMEOUT live-` | **unknown** (nicht in strings-Treffern) |
| `quiet`/`splash` Developer-Append aktiv | **no** (Cmdline ohne quiet/splash; memtest-Zeile enthält `nosplash`) |
| Marker im ISO | **unknown** (Squashfs; Tree ohne Marker-Kopie) |

## Bewertung

| Ampel | Bereich |
|-------|---------|
| **Grün** | Prepare-Tree: ISOLINUX Serial/Autoboot + Cmdline tty0/ttyS0 |
| **Rot** | ISO enthält Bootloader-Serial-Fix noch nicht — Rebuild blockiert |
| **Gelb** | Marker nur im Profil, nicht im materialisierten Tree |

## Abnahme

**Nicht erfüllt** für diesen Lauf: SHA256 unverändert; ISOLINUX-Serial nicht im ISO. Nach erfolgreichem Operator-Build erneut `strings` + SHA-Vergleich.

## QEMU-Smoke-Retry

**`blocked`** — erst nach neuem ISO-Build mit geänderter SHA256.
