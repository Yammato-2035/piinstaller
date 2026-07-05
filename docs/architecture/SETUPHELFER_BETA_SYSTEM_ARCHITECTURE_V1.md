# Setuphelfer Beta System Architecture V1

**Version:** 1.0 · **Status:** Architecture reference (public-safe)  
**Audience:** Developers, operators, security reviewers  
**Canonical contracts:** `backend/core/rescue_telemetry_client_contract_v2.py`, `backend/core/beta_agreement_gate_v1.py`

---

## 1. Purpose

The beta system connects **Rescue Stick** field diagnostics with **cloud-side ingestion**, **machine approval**, and a **hardware learning database** — without granting remote write access to customer machines. This document describes products, DNS boundaries, end-to-end data flow, and hard prohibitions.

---

## 2. Products and roles

| Product | Role | Runtime location |
|---------|------|------------------|
| **Setuphelfer (local)** | Installed assistant on target PC (`/opt/setuphelfer`) | Customer machine |
| **Rescue Stick** | Bootable live medium, offline-first diagnostics | USB / ISO |
| **Beta Registration Portal** | Account, MFA, agreement, stick registration | `beta.setuphelfer.de` (private deploy) |
| **Telemetry Server** | Signed ingest, quarantine, forward to diagnostics | `telemetry.setuphelfer.de` |
| **Diagnostics Server** | Hardware DB, learning import, matcher plane | `diagnose.setuphelfer.de` |
| **WordPress Bridge** | Marketing landing, deep-link to beta signup | Public CMS host |

Local Setuphelfer and Rescue Stick code live in the **public** repository. Server implementations live in **private** repositories (see `PUBLIC_PRIVATE_BOUNDARY_V1.md`).

---

## 3. Subdomains and trust zones

```
Internet (public)
  └── www.setuphelfer.de          WordPress / marketing
  └── beta.setuphelfer.de         Registration + attestation API (private)
  └── telemetry.setuphelfer.de    Ingest only — no command plane
  └── diagnose.setuphelfer.de     Learning import + hardware DB (private)

Lab placeholders (docs/tests only):
  telemetry.internal.setuphelfer.example
  diagnose.internal.setuphelfer.example
```

| Zone | TLS | Auth | Allowed callers |
|------|-----|------|-----------------|
| Beta portal | Required | User MFA + session | Browser, WP bridge |
| Telemetry ingest | Required | Stick HMAC/signature + event envelope | Rescue Stick only |
| Diagnostics import | Required | Service-to-service token | Telemetry server only |
| Local `/opt` API | Loopback/LAN policy | None (product default) | Local UI |

---

## 4. Data flow: Rescue Stick → Telemetry → Diagnostics

```
┌─────────────┐   redacted envelope    ┌──────────────────┐
│ Rescue Stick│ ─────────────────────► │ Telemetry Server │
│ (live boot) │   POST /v1/ingest      │  quarantine path │
└─────────────┘                        └────────┬─────────┘
       │                                        │
       │ local spool if offline                 │ accepted only if:
       ▼                                        │ stick verified,
  /setuphelfer/evidence/telemetry/              │ agreement valid,
  (USB persistence R3)                          │ machine approved
                                                ▼
                                       ┌──────────────────┐
                                       │ Diagnostics Srv  │
                                       │ learning/import  │
                                       └──────────────────┘
```

**Stages:**

1. **Collect (stick):** `system_assessment` built via `rescue_system_assessment_v2`, redacted per `assessment.redaction.v2`.
2. **Gate (stick):** `upload_allowed_for_mode()` checks stick attestation, beta agreement, machine approval.
3. **Ingest (telemetry):** Schema `telemetry.rescue.beta.v2`; unknown stick → `403`; missing agreement → `202 quarantine`.
4. **Forward (telemetry → diagnostics):** Only when ingest status is `accepted`; PII scan on diagnostics side rejects raw identifiers.
5. **Learn (diagnostics):** Hardware key correlation into `hardware_profiles` (see `DIAGNOSTICS_SERVER_HARDWARE_DB_BETA_0_1.md`).

Quarantine payloads are stored separately from accepted events and are **not** forwarded to the learning import until agreement and approval gates pass.

---

## 5. Stick types and attestation

| `stick_type` | Origin | Attestation |
|--------------|--------|-------------|
| `team_provisioned` | Pre-registered by operator, Type A | HMAC or signature with team key |
| `registered_iso` | User-registered ISO, Type B activation | Signature after portal pairing |
| `mock` | Lab / CI only | `attestation_mode: mock` |

See `BETA_STICK_REGISTRATION_AND_ATTESTATION_V1.md` and `beta_stick_activation_flow.md`.

---

## 6. Prohibitions (non-negotiable)

| ID | Rule |
|----|------|
| P-01 | Telemetry server **must not** expose execute/command/shell/fix routes (see mock `FORBIDDEN_PATH_PREFIXES`). |
| P-02 | Rescue Stick **must not** upload MAC, IP, email, plaintext serials, file lists, or secrets (`privacy.*` must be `false`). |
| P-03 | Beta registration **must not** collect identity document fields (`FORBIDDEN_ID_DOCUMENT_FIELDS`). |
| P-04 | Diagnostics learning import **rejects** payloads containing PII keys (`email`, `ip`, `mac`, …). |
| P-05 | Destructive repair actions remain `destructive_blocked` on beta sticks (`RESCUE_SAFE_ACTION_POLICY_V1.md`). |
| P-06 | Public repository **must not** contain production secrets, JWT keys, or private server code. |
| P-07 | Quarantined events **must not** enter hardware learning without explicit gate clearance. |
| P-08 | Remote operator write to target disks is **out of scope** for beta.0.1. |

---

## 7. Local mock stack (development)

| Service | Port | Module |
|---------|------|--------|
| Beta registration mock | 8100 | `backend/dev/beta_registration_mock_server_v1.py` |
| Telemetry mock v2 | 8101 | `backend/dev/telemetry_mock_server_v2.py` |
| Diagnostics mock v1 | 8102 | `backend/dev/diagnostics_mock_server_v1.py` |

Mocks have **no persistence** and must never be pointed at production domains. See also `BETA_DATA_FLOW_V1.md`, `SERVICE_INTERACTION_MATRIX_V1.md`, `RESCUE_TELEMETRY_CLIENT_CONTRACT_V2.md`.
