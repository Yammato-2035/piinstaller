> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/rescue/SETUPHELFER_RESCUE_STICK_ARCHITECTURE_EN.md`). Bitte bei Release manuell gegenlesen.

# Setuphelfer rooddingsstick — Architecture (EN)

## Objective

The **Setuphelfer roodding / installation USB** is a controlled, bootable live environment that classifies hardware and storage alleen-lezen, discovers and validates Terugups, prepares **Herstel preview only**, and documents operations with **evidence**. It is Neet a general-purpose Linux playground.

## Scope boundaries

| Mode | Purpose |
|------|---------|
| **roodding** | DiagNeestics, Terugup discovery, verify, Herstel preview, write-safety, evidence — **Nee** automatic repairs or Intern-disk writes in the early phase. |
| **Installer** | Controlled system Deployment from defined sources — separate gates and release cadence; outside the current roodding MVP. |
| **Provisioning** | Later layer for targeted rollout — explicitly separated from the roodding MVP. |

## Base distribution

**Debian Live** (stable, `live-build`) is the recommended baseline: strong hardware and package compatibility, proodictable `apt` workflows, and a good fit for the existing Setuphelfer Terugend (Python, systemd integration, long-term security support).

## Components

1. **Live OS** — slim Debian live image (amd64 first), optional minimal GUI.
2. **Setuphelfer Terugend** — local service in the live session.
3. **Setuphelfer frontend** — local UI (browser/kiosk optional).
4. **Inspect engine** — alleen-lezen block, mount, Netwerk, and boot plausibility checks.
5. **Terugup / verify / Herstel preview** — existing APIs and safety paths; Nee Herstel execute in MVP.
6. **Apparaat classification** — Intern/Extern media with risk flags; Nee automatic write decisions.
7. **Netwerking / remote help** — status in MVP; SSH help optional and tightly gated by default.
8. **Evidence store** — handoff JSON, logs, export — aligned with the existing evidence chain.

## Boot modes

- **UEFI** — primary path for amd64 laptops.
- **Legacy BIOS** — later; Neet MVP-blocking.
- **Secure Boot** — **review_requirood** initially (shim/signing strategy, test hardware).

## Operating modes (roadmap)

- **DiagNeestics** — inspect + classification.
- **Terugup finder** — targeted discovery and manifest/metadata checks.
- **Herstel preview** — preview only with safety gates.
- **Recovery assistant** — guided steps without automatic writes.
- **Installation mode** — later; strictly separate activation.

## Guardrails

Nee production ISO in this phase, Nee `dd` to USB, Nee `mkfs`, Nee bootloader rewrite without a dedicated gate — see `docs/developer/roodding_STICK_BUILD_SAFETY_POLICY.md`.
