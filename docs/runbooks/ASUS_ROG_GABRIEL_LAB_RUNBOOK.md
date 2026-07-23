# ASUS ROG Gabriel Lab Runbook

Profile: `ASUS_ROG_GABRIEL_LAB` (`config/lab-targets/asus-rog-gabriel.yaml`)

## Stick gate

1. Confirm Ultra Line stick: labels `SETUPHELFER` + `SETUP_LOGS`
2. Payload `1.10.3.1` — ESP `setuphelfer/rescue/rescue_payload_version` **and** squashfs `config/rescue_payload_version.json` must match
3. Squashfs SHA256 must match evidence `payload_squashfs.sha256`

## Identity gate

Before destructive/firmware/shell lab grants:

- exact manufacturer + G513QM + machine_id + system_uuid_hash
- disk roles via `nvme_identity_hash` (not `/dev/nvmeXnY` alone)
- roles remain `confirmed: false` until operator confirms → destructive Stage still blocked

## Critical path (current)

**A — instrumented Windows Setup live capture**

Deferred: BIOS 335, Mint on linux_lab_nvme.

## BitLocker

Read-only status allowed. Mutation always forbidden (API + shell guard).

Firmware/Secure-Boot/TPM changes may **indirectly** trigger recovery — warn first.

## Remote jobs

Use `/api/lab/jobs*` with signed, fingerprint-bound contracts. Wrong profile / expired / nonce replay → blocked.
