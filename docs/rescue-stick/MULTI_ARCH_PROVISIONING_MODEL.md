# Multi-Arch-Provisionierungsmodell — Rescue Stick

Stand: PI-RS-HW-COMPAT-PROVISION-001, Phase 19.

## Kernaussage

**Reale Betriebssysteminstallationen bleiben bis zur nächsten Freigabe
blockiert.** Diese Phase liefert ausschließlich einen Imagekatalog,
Kompatibilitätsprüfungen, eine Verifikationsvorschau und einen
Installationsplan — **kein** Schreibvorgang.

## Module

| Modul | Zweck |
|---|---|
| `backend/provisioning/os_catalog.py` | Lädt/filtert/validiert `data/provisioning/os_catalog.json`; erzwingt `download_enabled=false` |
| `backend/provisioning/os_compatibility.py` | Prüft Architektur/Plattform/Zielgröße gegen Katalogeintrag |
| `backend/provisioning/os_image_verifier.py` | SHA256-Berechnung für lokale Dateien, Verifikationsvorschau — **kein** Download |
| `backend/provisioning/os_install_plan.py` | Erzeugt `OsInstallPlan`-Vorschau, `write_allowed` immer `false` |

## Erste zulässige Katalogkategorien

**x86_64:** Debian Stable, Ubuntu LTS, Linux Mint Stable.

**ARM/Raspberry Pi:** Raspberry Pi OS, Debian ARM64, Ubuntu Server ARM64.

Weitere Kategorien (Proxmox, Fedora, openSUSE, CasaOS, YunoHost, Home
Assistant OS, weitere Appliance-Systeme) sind ausschließlich als
`support_status: "future"` vorbereitet.

## Katalogeintrag-Schema (`data/provisioning/os_catalog.schema.json`)

```json
{
  "image_id": "...",
  "display_name": "...",
  "distribution": "...",
  "release": "...",
  "architecture": "...",
  "image_type": "iso|raw_image|compressed_raw|netboot",
  "official_source": "...",
  "download_enabled": false,
  "sha256": "...",
  "signature_required": true,
  "signature_type": "...",
  "minimum_target_bytes": 0,
  "supported_platforms": [],
  "supported_boot_modes": [],
  "installation_method": "...",
  "support_status": "verified|experimental|future|blocked",
  "known_issues": [],
  "last_verified_at": null
}
```

## Provisionierungsplan

```json
{
  "plan_status": "ready_for_preview|review_required|blocked",
  "source_image": {},
  "target_platform": {},
  "target_device": {},
  "required_bytes": 0,
  "boot_mode": "...",
  "partition_plan_preview": [],
  "driver_plan": {},
  "firmware_plan": {},
  "post_install_plan": {},
  "write_allowed": false,
  "required_next_gates": []
}
```

`write_allowed` ist in dieser Phase **immer `false`** —
`backend/tests/test_provisioning_os_plan_v1.py` verifiziert dies
explizit für alle Pfade, auch bei ansonsten kompatiblen Zielsystemen.

## Nicht erlaubt in dieser Phase

- kein `dd` auf reale Zielmedien
- kein `mkfs`, `parted`, `sfdisk`, `sgdisk`, `wipefs`
- keine Änderung interner EFI-Partitionen
- keine automatische Betriebssysteminstallation
- kein Image-Download (`download_enabled` bleibt `false`)

## Nächster Meilenstein

`PI-RS-HW-ACTIVATE-002` behandelt den signierten Image-Download und den
kontrollierten Betriebssystem-Write ausschließlich auf explizit freigegebene
Testmedien, inklusive Verify und Bootnachweis.
