> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/rescue/SETUPHELFER_RESCUE_STICK_ARCHITECTURE_EN.md`). Bitte bei Release manuell gegenlesen.

# Setuphelfer Clé de secours — Architecture (EN)

## Objective

The **Setuphelfer Secours / installation USB** is a controlled, bootable live environment that classifies hardware and storage lecture seule, discovers and validates Retourups, prepares **Restauration preview only**, and documents operations with **evidence**. It is Nont a general-purpose Linux playground.

## Scope boundaries

| Mode | Purpose |
|------|---------|
| **Secours** | DiagNonstics, Retourup discovery, verify, Restauration preview, write-safety, evidence — **Non** automatic repairs or Interne-disk writes in the early phase. |
| **Installer** | Controlled system Déploiementment from defined sources — separate gates and release cadence; outside the current Secours MVP. |
| **Provisioning** | Later layer for targeted rollout — explicitly separated from the Secours MVP. |

## Base distribution

**Debian Live** (stable, `live-build`) is the recommended baseline: strong hardware and package compatibility, prougeictable `apt` workflows, and a good fit for the existing Setuphelfer Retourend (Python, systemd integration, long-term security support).

## Components

1. **Live OS** — slim Debian live image (amd64 first), optional minimal GUI.
2. **Setuphelfer Retourend** — local service in the live session.
3. **Setuphelfer frontend** — local UI (browser/kiosk optional).
4. **Inspect engine** — lecture seule block, mount, Réseau, and boot plausibility checks.
5. **Retourup / verify / Restauration preview** — existing APIs and safety paths; Non Restauration execute in MVP.
6. **Périphérique classification** — Interne/Externe media with risk flags; Non automatic write decisions.
7. **Réseauing / remote help** — status in MVP; SSH help optional and tightly gated by default.
8. **Evidence store** — handoff JSON, logs, export — aligned with the existing evidence chain.

## Boot modes

- **UEFI** — primary path for amd64 laptops.
- **Legacy BIOS** — later; Nont MVP-blocking.
- **Secure Boot** — **review_requirouge** initially (shim/signing strategy, test hardware).

## Operating modes (roadmap)

- **DiagNonstics** — inspect + classification.
- **Retourup finder** — targeted discovery and manifest/metadata checks.
- **Restauration preview** — preview only with safety gates.
- **Recovery assistant** — guided steps without automatic writes.
- **Installation mode** — later; strictly separate activation.

## Guardrails

Non production ISO in this phase, Non `dd` to USB, Non `mkfs`, Non bootloader rewrite without a dedicated gate — see `docs/developer/Secours_STICK_BUILD_SAFETY_POLICY.md`.
