# Rescue USB Write — Operator Handoff (Windows Inspect upstream)

**Track:** `rescue-stick` → `windows-laptop-rescue-inspect`  
**Status:** ISO validiert, **USB noch nicht geschrieben**  
**Agent/Cursor:** **kein** automatisches `dd`

## ISO (read-only verifiziert)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | ~488 MiB |
| SHA256 | `1899f5cabf9d40c9581805def9a765557a2168fc11ac181b0f71bfc0b1ff0691` |
| Typ | bootable hybrid ISO (`SETUPHELFER_RESCUE`) |
| Validator | `scripts/rescue-live/validate-rescue-iso-squashfs.sh` → Exit **0** (2026-06-05) |

## Warnung

Der USB-Stick wird **vollständig überschrieben**. Alle Daten auf dem Stick gehen verloren.

## Schritt 1 — Zielgerät identifizieren

**Vor** dem Einstecken:

```bash
lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN,TYPE,MOUNTPOINTS
```

USB-Stick einstecken, **erneut**:

```bash
lsblk -o NAME,SIZE,MODEL,SERIAL,TYPE,MOUNTPOINTS
```

Nur die **neu erschienene** externe Disk ist Kandidat. Bei Zweifel: **abbrechen**.

## Schritt 2 — Platzhalter ersetzen

```bash
ISO_PATH="/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
USB_DEV="/dev/REPLACE_WITH_CONFIRMED_USB_DEVICE"
```

- `USB_DEV` muss **extern/USB** sein — **niemals** interne NVMe/Systemplatten.
- Pfad auf dem **Operator-Rechner**, der den Stick schreibt (Developer-Maschine oder dedizierter Build-Host).

## Schritt 3 — Schreiben (nur Operator)

```bash
sudo dd if="$ISO_PATH" of="$USB_DEV" bs=4M status=progress conv=fsync
sync
```

**Nicht** aus Cursor/Agent ausführen.

## Schritt 4 — Nachprüfung

```bash
sync
sudo eject "$USB_DEV" 2>/dev/null || true
```

Stick abziehen, wieder einstecken. Optional SHA256 des Stick-Anfangs nicht nötig — Boot-Test ist Pflicht.

## Schritt 5 — Boot am Windows-11-Laptop

Siehe: `docs/evidence/windows-rescue/WINDOWS11_RESCUE_STICK_BOOT_AND_INSPECT_HANDOFF.md`

## Blocker bis erledigt

- `RESCUE_STICK_NOT_WRITTEN`
- `RESCUE_USB_BOOT_NOT_VALIDATED_ON_TARGET`

Erst danach: Windows read-only Inspect + Telemetrie.
