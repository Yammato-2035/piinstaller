# Rescue Remote Runbook Job Model

## Job-Schema

Felder: `job_id`, `created_at`, `expires_at`, `agent_id`, `runbook_id`, `mode`, `requires_operator_consent`, `command_plan` (leer in Phase 1), `timeout_seconds`, `redaction`, `status`, `result`.

## Phase-1 Runbooks (erlaubt)

| runbook_id | mode |
|------------|------|
| `collect_boot_logs` | read_only |
| `collect_network_status` | read_only |
| `collect_storage_inventory_readonly` | read_only |
| `collect_devserver_agent_logs` | diagnostic |
| `collect_qemu_or_rescue_agent_status` | diagnostic |
| `test_devserver_connectivity` | diagnostic |
| `upload_rescue_evidence_bundle` | diagnostic (Operator consent) |

## Verboten

`write_usb`, `restore_execute`, `mount_rw`, `partition_write`, `format`, `dd`, `mkfs`, `apt_install`, `shell`, `arbitrary_command`.

## Status

`queued` → `claimed` → `success` | `failed` | `timeout` | `blocked`
