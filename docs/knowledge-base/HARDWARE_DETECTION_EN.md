# Knowledge Base: Hardware Detection in the Rescue Stick

Status: PI-RS-HW-COMPAT-PROVISION-001, Phase 19. Audience: users and
support. No marketing language.
Languages: [Deutsch](HARDWARE_DETECTION_DE.md) · [English](HARDWARE_DETECTION_EN.md) · [Français](HARDWARE_DETECTION_FR.md) · [Nederlands](HARDWARE_DETECTION_NL.md)

## What does the Rescue Stick do with my hardware?

It detects devices in a read-only way via existing Linux mechanisms (sysfs,
PCI/USB IDs, kernel modalias) and evaluates their operational state in
multiple stages: detected → driver known → driver available → module
loaded → firmware present → ready. It makes **no** changes to your system.

## Does "detected" mean the device works?

**No.** Detection is the first step, not a functional guarantee. A device
can be detected while lacking a matching kernel module, missing firmware,
or being blocked by a boot parameter.

## What do the status lights mean?

- 🟢 Green: detected, driver loaded, firmware present, ready
- 🟡 Yellow: usable with limitations, optional driver, physical test needed
- 🔴 Red: driver/firmware missing, kernel incompatible, blocked
- ⚪ Gray: unknown, not checked, tool missing

## What is a "driver plan"?

A driver plan is a **proposal** for which driver/package would fit a
device — including the trust level of its source, license notes, and
Secure Boot impact. A driver plan is **not an installation**. This phase
has no "install driver" button, only "show driver plan".

## Why aren't printers/scanners always classified unambiguously?

Print technology (inkjet/laser/matrix) and color capability are only
derived from reliable sources (explicit IPP capabilities, CUPS/PPD
metadata, curated catalog) — never guessed from a model name. When the
data is insufficient, the system honestly reports `unknown`/
`review_required`.

## What happens with a multifunction device?

Printer, scanner, and any other functions of the same device are evaluated
**separately**. A working print function says nothing about the scan
function.

## Is Raspberry Pi 3–5 fully supported?

There is no blanket statement. Every combination of board, architecture,
operating system, and boot medium is evaluated individually. See
`docs/rescue-stick/RASPBERRY_PI_3_TO_5_SUPPORT_DE.md` for details.

## Why doesn't every OS image fit on the 64 GB stick?

A single 64 GB stick cannot hold unlimited full OS images. Setuphelfer
therefore uses a catalog of signed images with a bounded cache and
downloads images on demand instead of pre-installing everything. See
`docs/rescue-stick/64GB_CARRIER_ARCHITECTURE_DE.md` for details.

## Does this version already perform real installations?

**No.** This phase only delivers detection, classification, driver plans,
and an installation preview. No `dd`, no `mkfs`, no automatic installation.
Real, controlled write operations are deferred to a separate, explicitly
approved follow-up phase.

## Is my data (serial numbers, MAC addresses) transmitted?

No. Serial numbers, MAC addresses, IP addresses, full EDID data,
usernames/hostnames, and unique raw device identifiers are explicitly
excluded from telemetry (`backend/core/hardware_telemetry_contract.py`).
