# Developer Rescue ISO — Static Serial Validation

**Stand:** 2026-06-01  
**Build-Run:** `rescue_developer_iso_20260601_serial_visibility` (Build **nicht** ausgeführt)

## Live-Build-Tree (nach Prepare) — **grün**

| Kriterium | Ergebnis |
|-----------|----------|
| `console=ttyS0,115200n8` | **yes** (`auto/config`) |
| `console=tty0` | **yes** |
| `loglevel=7` / systemd debug | **yes** |
| `quiet splash` im Developer-Profil | **no** (nicht in `auto/config`) |
| `SETUPHELFER_BOOT_MARKER_START` | **yes** (includes.chroot) |
| `SETUPHELFER_AUTOPILOT_START` | **yes** |
| `SETUPHELFER_DEVSERVER_AGENT_START` | **yes** |

## ISO-Artefakt `binary.hybrid.iso` — **stale / alt**

Build nicht gestartet → ISO ist weiterhin Stand **07:54** (SHA256 `6a44d1fe…`).

`strings` auf bestehendem ISO:

| Kriterium | ISO strings |
|-----------|-------------|
| `console=ttyS0` | **yes** |
| `console=tty0` | **no** |
| `quiet splash` | **yes** (alter Boot-Pfad) |
| Autopilot-Marker | **no** (Squashfs nicht neu gebaut) |

**Bewertung:** Statische ISO-Validierung für Serial-Sichtbarkeit: **rot** (altes Image).  
Tree-Validierung: **grün** — nach Rebuild erwartet ISO-Strings analog zu `auto/config`.

## Nächster Schritt

Operator: sudo clean + controlled build (siehe `RESCUE_DEVELOPER_ISO_SERIAL_VISIBILITY_BUILD_RESULT.md`), dann diese Datei nach erneutem `strings`-Check aktualisieren.
