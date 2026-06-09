# RS-001 Live Medium Retest Handoff — React Launcher Fix 1.7.10.1

**Datum:** 2026-06-09  
**HEAD:** `dad1db5`  
**RS-001:** **yellow**  
**Ready for operator retest:** **false** (Payload-Update mit sudo ausstehend)

## SquashFS (Workspace, bereit)

```text
Version: 1.7.10.1
SquashFS: build/rescue/filesystem.squashfs.repacked-1.7.10.1
SHA256: 0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc
Alter Stick-Hash: a54aae1d902523cf08b37105b1f6001e048d610b57210520ea2e1a649b3fe820
```

## Schritt 1 — Payload auf Stick (Operator, sudo)

```bash
cd /home/volker/piinstaller

./scripts/rescue-live/update-fat32-esp-live-payload.sh \
  --target /dev/sdb \
  --new-squashfs build/rescue/filesystem.squashfs.repacked-1.7.10.1 \
  --operator-confirm-update \
  --confirm-phrase "UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD" \
  --execute-update

./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh \
  --target /dev/sdb \
  --expected-squashfs-sha256 0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc
```

Erwartung: `payload_update_status=success`, `verify_status=success`, kein `.sqtmp` auf Stick.

## Schritt 2 — Hardware-Retest

1. Rechner vollständig herunterfahren
2. Stick `/dev/sdb` (SETUPHELFER) einstecken
3. UEFI → USB/Setuphelfer → GRUB „Setuphelfer Rettung starten“
4. **Nichts** starten (kein Backup/Restore/Repair/Install)

## Erfolgskriterium (RS-001 green)

```text
Nutzbares Setuphelfer-Menü sichtbar (Kiosk-Browser ODER Fallback-TUI mit Auswahlmenü)
NICHT nur URL auf Konsole
Keine rohen failed-Units: network-onboarding, wait-online, telemetry-push im Anfängerflow
Kein whiptail-Blocker
```

## Bei Teil-Erfolg (yellow bleibt)

- Nur URL sichtbar → Launcher/Kiosk weiter prüfen
- Fallback-TUI sichtbar aber kein grafisches Menü → yellow (review_required), dokumentieren

## Dokumentation nach Retest

- `RS_001_REACT_RESCUE_HARDWARE_RETEST_RESULT.md`
- `RS_001_PHYSICAL_BOOT_RESULT.md`
- Evidence: `/run/setuphelfer/rescue-ui-status.json` oder Stick-Spiegel `setuphelfer/evidence/boot/`
