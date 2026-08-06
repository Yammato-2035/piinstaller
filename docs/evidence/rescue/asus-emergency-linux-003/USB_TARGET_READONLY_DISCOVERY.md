# USB_TARGET_READONLY_DISCOVERY — PI-RS-ASUS-CARRIER-BUILD-WRITE-004

Stand: 2026-08-06T20:54Z  
Modus: **nur lesend** — kein Write.

## Status

**`single_candidate_found`**

`write_allowed`: **false**

## Systemdatenträger

| Feld | Wert |
|------|------|
| Root | `/dev/nvme1n1p2` |
| System-Disk | `/dev/nvme1n1` (NVMe, nicht removable) |
| Weitere NVMe | `/dev/nvme0n1` (Windows/Daten-Partitionen, **kein** Write-Ziel) |

## USB-Kandidat (redigiert)

| Feld | Wert |
|------|------|
| Gerätepfad | `/dev/sda` |
| Hersteller | Intenso |
| Modell | Ultra Line |
| Kapazität | 63333990400 bytes (~58,98 GiB) — 64-GB-Klasse |
| Transport | `usb` |
| removable | true |
| Partitionen | 3 |
| Labels | `Linux Mint 22.3 Cinnamon 64-bit`, `writable` |
| Mounts | `/media/volker/Linux Mint 22.3 Cinnamon 64-bit`, `/media/volker/writable` |
| Setuphelfer-Carrier | **nein** (keine Carrier-Labels) |
| lokaler Fingerprint | `ce2e34b7f5ea4e41` (gesalzen; Rohserie **nicht** in Evidence) |

## Kapazität / Sicherheit (Phase 11)

| Feld | Wert |
|------|------|
| ISO-Größe | 1443889152 bytes |
| carrier_capacity_status | **passed** (Ziel ≫ ISO + 2 GiB Reserve) |
| target_safety_status | **review_required** (Ziel derzeit gemountet) |
| write_allowed | **false** |

Vor Write: Mounts kontrolliert aushängen, Identity Re-Read, zwei Operatorbestätigungen.

## Nicht-Ziele (explizit ausgeschlossen)

- `/dev/nvme1n1` — System
- `/dev/nvme0n1` — interne NVMe
- Auswahl nicht allein über „sda/sdb“-Reihenfolge, sondern über USB+removable+64‑GB-Klasse+Fingerprint
