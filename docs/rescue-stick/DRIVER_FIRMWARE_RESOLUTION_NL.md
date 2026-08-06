# Driver- en firmwareresolutie — Rescue Stick

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), uitgebreid met
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Talen: [Deutsch](DRIVER_FIRMWARE_RESOLUTION_DE.md) · [English](DRIVER_FIRMWARE_RESOLUTION_EN.md) · [Français](DRIVER_FIRMWARE_RESOLUTION_FR.md) · [Nederlands](DRIVER_FIRMWARE_RESOLUTION_NL.md)

Zie ook: [`docs/architecture/DRIVER_FIRMWARE_RESOLUTION_ARCHITECTURE.md`](../architecture/DRIVER_FIRMWARE_RESOLUTION_ARCHITECTURE.md).

## Doel

Ruwe hardware-inventariseringsgegevens worden een **voorstel** voor
driver-/firmwareactivering — zonder dit uit te voeren.

## Resolverstappen (`backend/core/driver_resolver.py`)

1. Kernel-modalias evalueren
2. Gebonden stuurprogramma controleren (`kernel_driver_in_use`)
3. Beschikbare kernelmodules controleren (`modinfo`/`lsmod`)
4. Firmwarefouten controleren (`backend/core/firmware_resolver.py`)
5. Geïnstalleerde pakketinformatie controleren
6. Distributie/architectuur meenemen
7. Gecureerde quirks toepassen (`hardware_compat_catalog.py`)
8. Veilig activeringsplan maken (`driver_activation_plan.py`)

Elke stap kan vroeg eindigen met `unknown` of `review_required` wanneer de
data ontoereikend is — Setuphelfer **raadt niet**.

## DriverPlan

`live_activation_possible` en `persistent_install_possible` zijn pure
beoordelingsvelden — geen module zet ze om in een echte actie.

## Vertrouwensniveaus van pakketbronnen

1. reeds aanwezig in de rescue-image
2. officiële distributierepositories
3. ondertekende Setuphelfer-offlinecache
4. officiële fabrikantrepository
5. handmatig aangeleverd ondertekend pakket
6. onbekende bron → **geblokkeerd**

## Expliciet verboden

- ongecontroleerde fabrikantshellscripts (`curl|bash`)
- download zonder checksum of zonder TLS
- automatisch toevoegen van pakketbronnen
- automatisch accepteren van licentievoorwaarden
- automatische installatie van proprietaire GPU-stuurprogramma's
- permanente kernelmodule-blacklists
- Secure Boot-/MOK-sleutelwijziging

## Firmwareresolver (`backend/core/firmware_resolver.py`)

Firmwarestatus wordt **apart** van driverstatus beoordeeld
(`present|missing|unknown|not_required`). Een geladen stuurprogramma zonder
passende firmware is `firmware_missing`, niet `ready`.
