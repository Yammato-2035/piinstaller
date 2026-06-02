# ISO-Precheck nach Deploy/Sync 55b7bce

**Stand:** 2026-06-02

| Kriterium | Status |
|-----------|--------|
| `release_restore_status` | **ok** |
| `profile_gate_status` | **green** |
| Fleet Heartbeat Live Smoke | **green** |
| DCC-Port-Mapping | **green** |
| Fleet-Script-Fix in `/opt` | **ok** (`55b7bce`) |
| Runtime-Code-Drift | **yellow** (4 nicht-kritische Dateien) |

## Freigaben

| Stufe | Status | Anmerkung |
|-------|--------|-----------|
| **Rescue-Agent Ingest Stub** | **`ready_for_rescue_agent_ingest_stub_smoke`** | **Primär — noch nicht ausgeführt** |
| **Controlled ISO build precheck** | **`ready_for_controlled_iso_build_precheck`** | **Folgeschritt nach Ingest**; read-only, **kein Build** |

## Weiterhin nicht grün

- Rescue ohne echtes ISO-/Boot-/USB-Artefakt
- E2EE: **contract_stub_only**
- nftables: **preview_only_apply_false**
- Rescue-Agent: Stub/Contract

## Guards (dieser Lauf)

Kein ISO-Build, kein controlled ISO build, kein QEMU, kein USB/dd, kein Backup, kein Restore.
