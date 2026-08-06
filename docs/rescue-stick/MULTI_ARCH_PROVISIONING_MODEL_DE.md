# Multi-Arch-Provisionierungsmodell — Rescue Stick

Stand: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), erweitert um
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Sprachen: [Deutsch](MULTI_ARCH_PROVISIONING_MODEL_DE.md) · [English](MULTI_ARCH_PROVISIONING_MODEL_EN.md) · [Français](MULTI_ARCH_PROVISIONING_MODEL_FR.md) · [Nederlands](MULTI_ARCH_PROVISIONING_MODEL_NL.md)

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
| `backend/provisioning/os_image_verifier.py` | SHA256 für lokale Dateien, Verifikationsvorschau — **kein** Download |
| `backend/provisioning/os_install_plan.py` | Erzeugt `OsInstallPlan`-Vorschau, `write_allowed` immer `false` |

## Erste zulässige Katalogkategorien

**x86_64:** Debian Stable, Ubuntu LTS, Linux Mint Stable.

**ARM/Raspberry Pi:** Raspberry Pi OS, Debian ARM64, Ubuntu Server ARM64.

Weitere Kategorien sind ausschließlich als `support_status: "future"` vorbereitet.

## Provisionierungsplan

`write_allowed` ist in dieser Phase **immer `false`** —
`backend/tests/test_provisioning_os_plan_v1.py` verifiziert dies explizit.

## Nicht erlaubt in dieser Phase

- kein `dd` auf reale Zielmedien
- kein `mkfs`, `parted`, `sfdisk`, `sgdisk`, `wipefs`
- keine Änderung interner EFI-Partitionen
- keine automatische Betriebssysteminstallation
- kein Image-Download (`download_enabled` bleibt `false`)

## Nächster Meilenstein

`PI-RS-HW-ACTIVATE-002` behandelt den signierten Image-Download und den
kontrollierten Betriebssystem-Write ausschließlich auf explizit freigegebene
Testmedien.
