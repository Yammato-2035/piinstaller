# Driver and Firmware Resolution — Rescue Stick

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), extended by
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Languages: [Deutsch](DRIVER_FIRMWARE_RESOLUTION_DE.md) · [English](DRIVER_FIRMWARE_RESOLUTION_EN.md) · [Français](DRIVER_FIRMWARE_RESOLUTION_FR.md) · [Nederlands](DRIVER_FIRMWARE_RESOLUTION_NL.md)

Related: [`docs/architecture/DRIVER_FIRMWARE_RESOLUTION_ARCHITECTURE.md`](../architecture/DRIVER_FIRMWARE_RESOLUTION_ARCHITECTURE.md).

## Purpose

Raw hardware inventory data becomes a **proposal** for driver/firmware
activation — without executing it.

## Resolver stages (`backend/core/driver_resolver.py`)

1. Evaluate kernel modalias
2. Check bound driver (`kernel_driver_in_use`)
3. Check available kernel modules (`modinfo`/`lsmod`)
4. Check firmware errors (`backend/core/firmware_resolver.py`)
5. Check installed package information
6. Consider distribution/architecture
7. Apply curated quirks (`hardware_compat_catalog.py`)
8. Produce a safe activation plan (`driver_activation_plan.py`)

Any stage may end early with `unknown` or `review_required` when data is
insufficient — Setuphelfer does **not** guess.

## DriverPlan

`live_activation_possible` and `persistent_install_possible` are assessment
fields only — no module turns them into a real action.

## Package source trust levels

1. already present in the rescue image
2. official distribution repositories
3. signed Setuphelfer offline cache
4. official vendor repository
5. manually provided signed package
6. unknown source → **blocked**

## Explicitly forbidden

- unchecked vendor shell scripts (`curl|bash`)
- download without checksum or without TLS
- automatic addition of package sources
- automatic acceptance of licence terms
- automatic installation of proprietary GPU drivers
- permanent kernel module blacklists
- Secure Boot/MOK key changes

## Firmware resolver (`backend/core/firmware_resolver.py`)

Firmware status is assessed **separately** from driver status
(`present|missing|unknown|not_required`). A loaded driver without matching
firmware is `firmware_missing`, not `ready`.
