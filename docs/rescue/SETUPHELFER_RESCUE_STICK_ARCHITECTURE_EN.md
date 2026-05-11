# Setuphelfer Rescue Stick — Architecture (EN)

## Objective

The **Setuphelfer rescue / installation USB** is a controlled, bootable live environment that classifies hardware and storage read-only, discovers and validates backups, prepares **restore preview only**, and documents operations with **evidence**. It is not a general-purpose Linux playground.

## Scope boundaries

| Mode | Purpose |
|------|---------|
| **Rescue** | Diagnostics, backup discovery, verify, restore preview, write-safety, evidence — **no** automatic repairs or internal-disk writes in the early phase. |
| **Installer** | Controlled system deployment from defined sources — separate gates and release cadence; outside the current rescue MVP. |
| **Provisioning** | Later layer for targeted rollout — explicitly separated from the rescue MVP. |

## Base distribution

**Debian Live** (stable, `live-build`) is the recommended baseline: strong hardware and package compatibility, predictable `apt` workflows, and a good fit for the existing Setuphelfer backend (Python, systemd integration, long-term security support).

## Components

1. **Live OS** — slim Debian live image (amd64 first), optional minimal GUI.
2. **Setuphelfer backend** — local service in the live session.
3. **Setuphelfer frontend** — local UI (browser/kiosk optional).
4. **Inspect engine** — read-only block, mount, network, and boot plausibility checks.
5. **Backup / verify / restore preview** — existing APIs and safety paths; no restore execute in MVP.
6. **Device classification** — internal/external media with risk flags; no automatic write decisions.
7. **Networking / remote help** — status in MVP; SSH help optional and tightly gated by default.
8. **Evidence store** — handoff JSON, logs, export — aligned with the existing evidence chain.

## Boot modes

- **UEFI** — primary path for amd64 laptops.
- **Legacy BIOS** — later; not MVP-blocking.
- **Secure Boot** — **review_required** initially (shim/signing strategy, test hardware).

## Operating modes (roadmap)

- **Diagnostics** — inspect + classification.
- **Backup finder** — targeted discovery and manifest/metadata checks.
- **Restore preview** — preview only with safety gates.
- **Recovery assistant** — guided steps without automatic writes.
- **Installation mode** — later; strictly separate activation.

## Guardrails

No production ISO in this phase, no `dd` to USB, no `mkfs`, no bootloader rewrite without a dedicated gate — see `docs/developer/RESCUE_STICK_BUILD_SAFETY_POLICY.md`.
