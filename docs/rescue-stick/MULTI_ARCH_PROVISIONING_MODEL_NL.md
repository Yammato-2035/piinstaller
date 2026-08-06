# Multi-arch-provisioneringsmodel — Rescue Stick

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), uitgebreid met
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Talen: [Deutsch](MULTI_ARCH_PROVISIONING_MODEL_DE.md) · [English](MULTI_ARCH_PROVISIONING_MODEL_EN.md) · [Français](MULTI_ARCH_PROVISIONING_MODEL_FR.md) · [Nederlands](MULTI_ARCH_PROVISIONING_MODEL_NL.md)

## Kernboodschap

**Echte besturingssysteeminstallaties blijven geblokkeerd tot de volgende
vrijgavepoort.** Deze fase levert uitsluitend een imagecatalogus,
compatibiliteitscontroles, een verificatievoorbeeld en een installatieplan —
**geen** schrijfactie.

## Modules

| Module | Doel |
|---|---|
| `backend/provisioning/os_catalog.py` | Laadt/filtert/valideert `data/provisioning/os_catalog.json`; dwingt `download_enabled=false` af |
| `backend/provisioning/os_compatibility.py` | Controleert architectuur/platform/doelgrootte tegen catalogusitem |
| `backend/provisioning/os_image_verifier.py` | SHA256 voor lokale bestanden, verificatievoorbeeld — **geen** download |
| `backend/provisioning/os_install_plan.py` | Maakt `OsInstallPlan`-voorbeeld, `write_allowed` altijd `false` |

## Eerste toegestane cataloguscategorieën

**x86_64:** Debian Stable, Ubuntu LTS, Linux Mint Stable.

**ARM/Raspberry Pi:** Raspberry Pi OS, Debian ARM64, Ubuntu Server ARM64.

Verdere categorieën zijn uitsluitend voorbereid als `support_status: "future"`.

## Provisioneringsplan

`write_allowed` is in deze fase **altijd `false`** —
`backend/tests/test_provisioning_os_plan_v1.py` verifieert dit expliciet.

## Niet toegestaan in deze fase

- geen `dd` op echte doelmedia
- geen `mkfs`, `parted`, `sfdisk`, `sgdisk`, `wipefs`
- geen wijziging van interne EFI-partities
- geen automatische OS-installatie
- geen imagedownload (`download_enabled` blijft `false`)

## Volgende mijlpaal

`PI-RS-HW-ACTIVATE-002` behandelt de ondertekende imagedownload en gecontroleerde
OS-schrijfactie uitsluitend op expliciet goedgekeurde testmedia.
