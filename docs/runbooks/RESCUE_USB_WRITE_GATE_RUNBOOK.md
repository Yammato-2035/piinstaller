# Runbook — Rescue USB Write Gate

**Version:** 1.0
**usb_write_allowed:** `false` (bis explizite Operator-Bestätigung)
**real_iso_build_allowed:** `false` (ISO muss zuerst gebaut und geprüft sein)

## Zweck

Definiert **manuelle** Schritte zum Schreiben einer Rescue-ISO auf ein USB-Ziel — **kein** automatisches Script, **kein** dd ohne Operator.

## Voraussetzungen

1. Erfolgreicher ISO-Build (separater Auftrag mit Operator-Freigabe)
2. ISO-SHA256 dokumentiert und verifiziert
3. Phase 0 Runtime-Gate (Dev-Repo) — optional für USB-Phase, aber empfohlen
4. **Zweifache** Bestätigung des Zielgeräts durch Operator

## Zielgerät identifizieren

```bash
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL,SERIAL
```

**Pflicht:**

- Interne Systemdisk **ausschließen** (NVMe/SSD mit `/`, `/boot`, `/home`)
- Nur explizit freigegebenes USB-Ziel wählen
- `MOUNTPOINT` leer oder nur temporäre Live-Mounts — **nicht** Produktivdaten

## SHA256 prüfen

```bash
sha256sum /path/to/live-image-amd64.hybrid.iso
# Abgleich mit dokumentierter Evidence
```

## Schreib-Befehl (NUR Template — NICHT automatisch ausführen)

```bash
# OPERATOR: Ziel /dev/XXXX durch freigegebenes Gerät ersetzen
# OPERATOR: zweite Bestätigung (Seriennummer, Größe, lsblk)
sudo dd if=/path/to/live-image-amd64.hybrid.iso of=/dev/<TARGET> bs=4M status=progress conv=fsync
```

## Verboten

- Kein Script im Repo, das `dd` ausführt
- Kein automatisches USB-Schreiben
- Kein `mkfs` / `parted write` ohne separates Gate
- Kein Schreiben auf unbestätigtes Gerät

## Nach USB-Write

1. Medium physisch booten
2. Live-Evidence: `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md`
3. Temp-Runtime local-only prüfen (`check-localonly.sh`)

## Development Dashboard

- USB-Write-Status: Cockpit-Panel **Rettungsstick Build** (`usb_write_gate` rot/blockiert)
- Kein USB-Write-Button im Dashboard — separates Operator-Gate bleibt

## Referenzen

- `RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`
- `RESCUE_TEMP_RUNTIME_COPY_TO_LIVE_MEDIUM.md` (Bundle-only, kein dd)
