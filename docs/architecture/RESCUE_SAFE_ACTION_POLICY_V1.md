# Rescue Safe Action Policy V1

**Version:** 1.0 · **Implementation:** `backend/core/rescue_safe_action_model_v1.py`  
**Scope:** Rescue Stick live environment — beta and release builds

---

## 1. Purpose

Rescue must help operators **without** silently modifying customer disks or boot structures. Actions are classified into five **safe action classes**. Destructive IDs are hard-blocked regardless of UI affordances.

---

## 2. Action classes

| Class | Value | Meaning | Operator confirm |
|-------|-------|---------|------------------|
| **Explain only** | `explain_only` | Textual guidance, no system change | No |
| **Local rescue fix** | `local_rescue_fix` | Reversible change on **live** stick environment only | Usually no |
| **Target read-only advice** | `target_readonly_advice` | Guidance about mounted target, no writes | No |
| **Operator confirmed low risk** | `operator_confirmed_low_risk_fix` | Small fix after explicit confirm | **Yes** |
| **Destructive blocked** | `destructive_blocked` | Never executed on beta stick | N/A (blocked) |

---

## 3. Class behavior matrix

| Class | Writes to target disk | Writes to stick live FS | Telemetry impact |
|-------|----------------------|-------------------------|------------------|
| `explain_only` | No | No | None |
| `local_rescue_fix` | No | Yes (live session) | May trigger re-assessment |
| `target_readonly_advice` | No | No | None |
| `operator_confirmed_low_risk_fix` | No* | Maybe | Logged in evidence |
| `destructive_blocked` | **Blocked** | **Blocked** | Block event logged |

\*Low-risk fixes must not appear in `DESTRUCTIVE_ACTION_IDS`. Any target write capability requires explicit future policy revision.

---

## 4. Catalogued local safe actions

| `action_id` | Class | Reversible | Evidence required |
|-------------|-------|------------|-------------------|
| `restart_network_manager_live` | `local_rescue_fix` | Yes | Yes |
| `rfkill_soft_unblock_wifi` | `local_rescue_fix` | Yes | Yes |
| `wlan_rescan` | `local_rescue_fix` | Yes | No |
| `retry_telemetry_queue` | `local_rescue_fix` | Yes | Yes |
| `repair_setup_logs_evidence_path` | `local_rescue_fix` | Yes | Yes (SETUP_LOGS only) |
| `restart_kiosk_service_live` | `local_rescue_fix` | Yes | Yes |

---

## 5. Destructive blocked IDs

The following IDs always resolve to `destructive_blocked` (even if not in `SAFE_ACTION_CATALOG`):

```
efi_repair, bootloader_write, partition_modify, filesystem_repair,
target_apt_install, malware_remove, windows_modify, linux_target_write,
dd, mkfs, wipefs, parted_write, restore_original_device
```

Example catalog entry: `efi_repair` — titles indicate blocked state in DE/EN.

---

## 6. Decision rules

```python
# Simplified policy
if action_id in DESTRUCTIVE_ACTION_IDS:
    return DESTRUCTIVE_BLOCKED
if requires_operator_confirmation and not operator_confirmed:
    return BLOCKED_PENDING_CONFIRM
if action_class == LOCAL_RESCUE_FIX:
    return ALLOWED_ON_LIVE_ONLY
```

`action_allowed_without_operator()` returns `False` for unknown IDs, destructive class, or actions with `requires_operator_confirmation=True`.

---

## 7. SafeActionPlanItem (UI / API)

Each planned action exposes:

- `action_id`, `action_class`, `status`  
- `reason_de`, `reason_en`  
- `operator_confirmed`, `evidence_ref`  

Statuses include: `planned`, `blocked`, `completed`, `failed`, `cancelled`.

---

## 8. Beta-specific notes

- Beta sticks **must not** downgrade destructive blocks for “testing.”  
- Telemetry upload (`retry_telemetry_queue`) is allowed — it does not modify target disks.  
- Repair advice engine (`rescue_repair_advice_engine_v1`) may only **recommend** `explain_only` or `target_readonly_advice` for blocked destructive IDs.

---

## 9. Evidence requirements

When `evidence_required=True`, the stick must reference a spool path or boot session ID before execution. Fail closed if evidence path is missing.

---

## 10. Related documents

- `RESCUE_HARDSTOPS.md`  
- `RESCUE_OPERATOR_POLICY.md`  
- `SETUPHELFER_BETA_SYSTEM_ARCHITECTURE_V1.md` (prohibition P-05)
