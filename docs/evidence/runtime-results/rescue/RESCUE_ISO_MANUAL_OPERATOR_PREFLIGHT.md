# Rescue ISO Manual Operator — Preflight

**HEAD:** `11e27b6` · **2026-05-27**

## Phase-0

`./scripts/check-runtime-deploy-gate.sh` → **Exit 0** · `deploy_drift` **green** · `safe_test_mode` **UNLOCKED**

## Dashboard (read-only)

| Check | Wert |
|-------|------|
| `runtime_gate.passed` | **true** |
| `deploy_drift.status` | **green** |
| `release_gate_status` | **rot** (Recovery-Core) |
| Rescue area (roadmap) | **blocked** |
| Verify area (roadmap) | **blocked** |

## Verify vs. Subsystem-Green

**„Verify subsystem green“ ≠ „BR-001 Verify Deep green“.**  
Grüne Runtime-/Consistency-Checks betreffen nur Phase-0/Deploy-Readiness. BR-004/BR-005 und Verify Deep bleiben an gültigem BR-001-OFFLINE-Archiv gebunden (roadmap **blocked**).

## Fortsetzung

Preflight **allowed_to_continue: true** — Build-Versuch folgt in Phase 2–4 (Operator-TTY erforderlich).

JSON: `rescue_iso_manual_operator_preflight_latest.json`
