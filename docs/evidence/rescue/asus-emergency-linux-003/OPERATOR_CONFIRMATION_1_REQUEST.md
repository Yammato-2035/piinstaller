# OPERATOR-BESTÄTIGUNG 1 — erforderlich vor USB-Write

## WARNUNG

Alle Daten auf dem unten genannten USB-Ziel werden **unwiderruflich gelöscht**
(aktuell u. a. Linux-Mint-Live-Medium + `writable`-Partition).

Interne NVMe (`nvme0n1`, `nvme1n1`) werden **nicht** beschrieben.

## ISO / Build

| Feld | Wert |
|------|------|
| ISO-Pfad | `/home/volker/piinstaller-asus-emergency-linux-telemetry-003/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| ISO-SHA256 | `ce3258f945ea2f973414ed6bdca29f884be9415f66e06a0e9110e6d6b0f87473` |
| Build-ID / Run-ID | `asus-carrier-004-20260806T195318Z` |
| Payload-Version (SoT) | `1.10.0.17` |
| Projektversion | `1.10.2.0` |
| Git-Commit (Bundle) | `2deb694b` |

## USB-Ziel

| Feld | Wert |
|------|------|
| Gerätepfad | `/dev/sda` |
| Hersteller | Intenso |
| Modell | Ultra Line |
| Kapazität | 63333990400 bytes (~58,98 GiB) |
| Partitionen | sda1 (iso9660, gemountet), sda2 (vfat), sda3 (ext4 `writable`, gemountet) |
| Labels | `Linux Mint 22.3 Cinnamon 64-bit`, `writable` |
| lokaler Fingerprint | `ce2e34b7f5ea4e41` |

## Erforderliche Antwort (ausdrücklich)

Bitte antworten mit **genau**:

1. dem Gerätepfad: `/dev/sda`
2. der kurzen Zielkennung: `Intenso Ultra Line` **oder** Fingerprint `ce2e34b7f5ea4e41`
3. dem Satz: `BESTÄTIGUNG 1: USB-ZIEL KORREKT`

Ohne diese drei Bestandteile erfolgt **kein** Write und **kein** automatisches Aushängen.
