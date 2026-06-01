# Development Diagnostic Export — Contract

**Scope:** `local_lab_only` — read-only, redacted by default.

## Export types

| Type | Endpoint / builder | Purpose |
|------|-------------------|---------|
| `fleet_session_summary` | `GET …/fleet-sessions/{id}/export` | Fleet session + linked QEMU evidence |
| `qemu_smoke_diagnostics` | `GET …/qemu-smokes/{run_id}/export` | Full QEMU smoke diagnostic JSON |
| `devserver_node_ingest_diagnostics` | Embedded in QEMU export | `devserver_ingest` block |
| `runtime_gate_snapshot` | Embedded `runtime` | Version metadata (gate not re-run) |
| `evidence_bundle_index` | `GET …/evidence-index` | File list + sizes, no binary payload |
| `markdown_report` | `GET …/markdown` | Human-readable report |

## Response codes

| Code | Meaning |
|------|---------|
| `DEV_DIAGNOSTIC_EXPORT_OK` | Export ready (unredacted flag) |
| `DEV_DIAGNOSTIC_REDACTED` | Export ready, redacted |
| `DEV_DIAGNOSTIC_MARKDOWN_OK` | (markdown body; plain text response) |
| `DEV_DIAGNOSTIC_EVIDENCE_INDEX_OK` | Index only |
| `DEV_DIAGNOSTIC_NOT_FOUND` | Session/run/evidence missing |
| `DEV_DIAGNOSTIC_BLOCKED_UNREDACTED_NOT_CONFIRMED` | `redacted=false` without operator confirm |
| `DEV_DIAGNOSTIC_DISABLED` | Feature disabled |

## JSON schema (required top-level)

```json
{
  "export_id": "diag-{run_id}-{suffix}",
  "created_at": "ISO-8601",
  "redacted": true,
  "scope": "local_lab_only",
  "sharing_warning": "Internal development data. Do not publish.",
  "run_id": "qemu_rescue_…",
  "session_id": "fleet-{run_id}",
  "classification": {
    "primary": "serial_empty_boot_unknown",
    "secondary": ["devserver_ingest_missing"],
    "confidence": "high|medium|low"
  },
  "runtime": { "gate_status": "not_re_evaluated_in_export", "api_version": {} },
  "fleet_session": {},
  "qemu_smoke": {
    "autopilot_result": {},
    "qemu_exit_code": 124,
    "serial_size_bytes": 0,
    "serial_excerpt_head": "",
    "serial_excerpt_tail": ""
  },
  "devserver_ingest": {
    "report_new": false,
    "guest_found": false
  },
  "evidence": { "paths": [], "missing_paths": [], "bundle_available": false },
  "redaction": { "rules_applied": [], "secrets_detected": false, "warnings": [] }
}
```

## Redaction rules

- Remove/mask API keys, bearer tokens, private keys, generic `token=` / `secret=` patterns
- Mask email addresses
- Lab IPs `127.0.0.1` and `10.0.2.2` allowed
- Serial log: max 80 head + 160 tail lines; per-line truncation
- No full binary logs in export

## Unredacted access

`?redacted=false&operator_confirm_unredacted_local_only=true` — local operator only.

## Forbidden

- No POST control routes (start/stop/QEMU/deploy/backup/restore)
- No secrets in export
- No public product documentation as GA feature
