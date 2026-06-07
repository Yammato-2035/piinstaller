# USB-Rewrite-Handoff — nach Telemetrie-Automatisierung (1.7.6.0)

**Kein dd durch Agent.** Nur Operator-Anleitung.

## Kanonische ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| **SHA256** | **`80508492a8f3187e79bb700675d81eac3e19f8e5647bb5b4a84febcf6c8b32f0`** |
| Größe | **683671552** bytes |

Vorherige Stick-ISO (1.7.5.0): `86cba7eb550bcdb0562a414f79d78db58c908d5d743d474365eda0bcb638e5fc`

## Ziel-Stick (read-only erfasst)

| Feld | Wert |
|------|------|
| Gerät | **`/dev/sdb`** |
| Modell | Ultra Line |
| Serial | `24111412110212` |
| Aktuell gemountet | `/media/gabriel/SETUPHELFER_RESCUE` |

**Nicht** `/dev/sda` (Backup-Platte) verwenden.

## Operator — Rewrite

```bash
cd /home/volker/piinstaller
ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
TARGET=/dev/sdb

sha256sum "$ISO"
# Erwartung: 80508492a8f3187e79bb700675d81eac3e19f8e5647bb5b4a84febcf6c8b32f0

stat -c '%s bytes' "$ISO"
lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN,FSTYPE,LABEL,MOUNTPOINTS /dev/sda /dev/sdb

udisksctl unmount -b /dev/sdb1 2>/dev/null || true
sync
sudo dd if="$ISO" of="$TARGET" bs=4M status=progress conv=fsync
sync
```

## Operator — Block-Readback SHA256

```bash
ISO_SIZE=$(stat -c '%s' "$ISO")
sudo python3 - <<PY
import hashlib
from pathlib import Path
size=int("$ISO_SIZE")
h=hashlib.sha256()
remaining=size
with Path("/dev/sdb").open("rb", buffering=0) as f:
    while remaining:
        chunk=f.read(min(4194304, remaining))
        if not chunk:
            break
        h.update(chunk)
        remaining-=len(chunk)
print(h.hexdigest())
PY
# Erwartung: 80508492a8f3187e79bb700675d81eac3e19f8e5647bb5b4a84febcf6c8b32f0
```

## Vor MSI-Boot (Developer-Laptop)

```bash
SETUPHELFER_RESCUE_TELEMETRY_BIND=192.168.178.140 \
  ./scripts/rescue-live/start-rescue-telemetry-lan-proxy.sh
curl -fsS http://192.168.178.140:8001/api/rescue/telemetry/health
```

Optional WLAN ohne MSI-Tippen: USB-Ordner `SETUPHELFER_RESCUE_CONFIG/network.env` mit `SETUPHELFER_RESCUE_WIFI_SSID` und lokaler `SETUPHELFER_RESCUE_WIFI_PSK_FILE` (Passwort **nicht** ins Repo).

## Nach USB-Rewrite — erwartetes MSI-Verhalten

1. Boot vom Stick (Default-Eintrag reicht; systemd startet Onboarding + Telemetrie automatisch).
2. WLAN verbindet (bekanntes Profil oder vorbereitete `network.env`).
3. `setuphelfer-rescue-telemetry-push` läuft ohne SyntaxError; bei Offline Spool + Retry-Timer.
4. Health über `http://192.168.178.140:8001/api/rescue/telemetry/health`, Ingest ACK auf Developer-Laptop.

**Kein manuelles curl/python auf dem MSI als Regelablauf.**

## Nächster Prompt

Nach Readback grün: **`RESCUE_MSI_BOOT_AUTOMATED_TELEMETRY_ACK_OPERATOR_RUN`**
