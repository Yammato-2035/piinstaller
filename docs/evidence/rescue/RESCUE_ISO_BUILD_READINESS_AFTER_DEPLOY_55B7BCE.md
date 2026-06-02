# ISO-Precheck nach Deploy/Sync 55b7bce

**Stand:** 2026-06-02

| Kriterium | Status |
|-----------|--------|
| Fleet-Script-Fix in `/opt` | **ok** |
| Fleet Heartbeat Live Smoke | **ok** |
| Release-Profil wiederhergestellt | **ok** |
| Profile gate | **green** |
| DCC-Port-Mapping | **green** |
| Runtime-Code-Drift | **yellow** (4 nicht-kritische UI/Script-Dateien) |

## Freigaben

| Stufe | Status |
|-------|--------|
| Rescue-Agent Ingest Stub | **`ready_for_rescue_agent_ingest_stub_smoke`** |
| Controlled ISO build precheck | **`ready_for_controlled_iso_build_precheck`** (read-only, **kein Build**) |

## Weiterhin nicht grün

- Rescue-Gesamtstatus ohne echtes ISO-/Boot-/USB-Artefakt
- E2EE: **contract_stub_only**
- nftables: **preview_only_apply_false**
- Rescue-Agent: Stub/Contract

## Nicht in diesem Lauf

Kein ISO-Build, kein controlled ISO build, kein QEMU/USB.
