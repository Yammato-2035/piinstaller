# Rescue Agent Dashboard (Stub)

Status: **UI-Stub integriert** (`RescueAgentPanel`), keine Fake-VM-Erzeugung.

## Sichtbare Status

- `pending_pairing`, `paired`, `heartbeat_seen`, `report_received`
- `e2ee_required`, `e2ee_ok`, `firewall_policy_ready`
- `offline`, `timeout`

## Angezeigte Daten (Stub)

- Session/Agent-Identität, Heartbeat, Pairing-Status
- E2EE-Pflichtstatus, Firewall-Pflichtstatus
- Keine automatische Standortbehauptung
- Standort nur über `operator_label`/`site_hint`
