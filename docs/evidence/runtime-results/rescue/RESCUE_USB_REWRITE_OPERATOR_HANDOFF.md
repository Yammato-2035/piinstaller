# RESCUE USB Rewrite — Operator Handoff (ISO 1.7.5.0 Network Onboarding)

**Status:** Freigegeben nach Post-Build-Validierung  
**Datum:** 2026-06-07  
**Voraussetzung:** `RESCUE_ISO_NETWORK_ONBOARDING_POST_BUILD_VALIDATION_RESULT.md` grün

## ISO (Ziel)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `86cba7eb550bcdb0562a414f79d78db58c908d5d743d474365eda0bcb638e5fc` |
| Größe | 683671552 bytes |
| UEFI | validiert (Exit 0 inkl. Post-Patch) |
| Network-Onboarding | im SquashFS verifiziert |

## USB-Stick (Zielgerät)

| Feld | Wert |
|------|------|
| Device | `/dev/sdb` (Operator bestätigen!) |
| Modell | Ultra Line |
| Serial | `24111412110212` |
| Aktueller Inhalt | **alte ISO** `9ef1b330…` — muss überschrieben werden |

**Nicht Ziel:** `/dev/sda`, `/dev/nvme*`, Backup-Datenträger.

---

## Phase 1 — Developer-Laptop (vor MSI-Boot)

Proxy muss laufen:

```bash
cd /home/volker/piinstaller
SETUPHELFER_RESCUE_TELEMETRY_BIND=192.168.178.140 ./scripts/rescue-live/start-rescue-telemetry-lan-proxy.sh
./scripts/rescue-live/status-rescue-telemetry-lan-proxy.sh
curl -sS http://192.168.178.140:8001/api/rescue/telemetry/health | jq .
```

---

## Phase 2 — USB schreiben (Operator, manuell)

**Agent/Cursor führt kein dd aus.**

```bash
cd /home/volker/piinstaller
ISO="build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"

# SHA256 vor Write prüfen:
sha256sum "$ISO"
# Erwartung: 86cba7eb550bcdb0562a414f79d78db58c908d5d743d474365eda0bcb638e5fc

# Stick sicher auswerfen falls gemountet:
udisksctl power-off -b /dev/sdb 2>/dev/null || true

# NUR wenn /dev/sdb der Ultra-Line-Stick ist:
sudo dd if="$ISO" of=/dev/sdb bs=4M status=progress conv=fsync
sync
```

---

## Phase 3 — Readback / Gate (Operator)

```bash
# Block-Readback SHA256 (Beispiel — Operator-Policy beachten):
sudo dd if=/dev/sdb of=/tmp/rescue_usb_readback.img bs=4M status=progress count=<ISO_BLOCK_COUNT>
sha256sum /tmp/rescue_usb_readback.img
# Muss 86cba7eb… sein

# Boot-Artefakte (read-only Mount):
sudo mount -o ro /dev/sdb1 /mnt
ls -la /mnt/EFI/BOOT/BOOTX64.EFI /mnt/boot/grub/efi.img /mnt/isolinux/isolinux.bin
sudo umount /mnt
```

Evidence ingestieren → `usb_write_sha256_verified=true` setzen.

---

## Phase 4 — MSI-Boot + Netzwerk + Telemetrie

1. MSI vom Stick booten (UEFI, Secure Boot aus)
2. Im Live-System:

```bash
sudo setuphelfer-rescue-network-onboarding
# oder: setuphelfer-network
sudo setuphelfer-rescue-media-check
sudo setuphelfer-rescue-telemetry-push
sudo setuphelfer-rescue-task-pull
curl -i http://192.168.178.140:8001/api/rescue/telemetry/health
```

3. Kein WLAN-Passwort in Logs/Evidence.

---

## Gate nach Erfolg

Erst dann:

- `usb_write_sha256_verified=true`
- `target_network_link_established=true` (wenn MSI-Netz ok)
- `target_telemetry_health_reached=true` / `target_telemetry_ingest_ack=true`

**Windows-Inspect bleibt blockiert**, bis alle Telemetrie-Gates grün.

---

## Nächster Prompt nach USB-Write

`RESCUE_USB_MSI_UEFI_BOOT_NETWORK_TELEMETRY_OPERATOR_RUN`

## Verboten

Windows-Inspect, Partitionieren, Backup/Restore, Agent-dd.
