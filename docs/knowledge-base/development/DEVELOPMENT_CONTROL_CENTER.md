# Knowledge Base: Development Control Center

## Kurzfassung

Das **Development Control Center** ist die externe Governance-Ansicht für Setuphelfer-Entwicklung. Es nutzt dieselbe Datenlage wie das Development Cockpit (`loadDevDashboard`), ergänzt um eine **16-Bereiche-Matrix**, **Alerts**, **Timeline** und **Governance Meta-Prompt**.

## Wann Runtime, wann Standalone?

| Signal | Bedeutung |
|--------|-----------|
| `source=runtime_api` | Produktives Backend; Gates gültig für Phase 0 |
| `standalone_workspace` / `snapshot` | Nur Workspace; Runtime-Gate **nicht** bestanden |
| `apiReachable=false` | Matrix markiert Runtime rot; Safe Test **LOCKED** |

## Operative Reihenfolge

1. `sudo ./scripts/deploy-to-opt.sh <repo>`
2. `sudo ./scripts/write-dev-workspace-systemd-dropin.sh` (bei Workspace unter `/home`)
3. `sudo systemctl restart setuphelfer-backend.service`
4. `./scripts/check-runtime-deploy-gate.sh`
5. Control Center öffnen und Matrix/Timeline beobachten

## Evidence & rote Module

Release-Gates unter `docs/evidence/release-gates/` (z. B. `backup_restore_release_gate.json`) bleiben **rot**, solange BR-001 offen ist — **kein UI-Fehler**. `tests_evidence` kann **gelb** sein (pytest ok, Release blockiert). Runtime-Gate grün ≠ BR-001 freigegeben.

Rückkehrplan: [CORE_RECOVERY_TEST_RETURN.md](./CORE_RECOVERY_TEST_RETURN.md)

## Verweise

- [dev-dashboard/README.md](../../dev-dashboard/README.md)
- [EXTERNAL_CONTROL_CENTER_DE.md](../../dev-dashboard/EXTERNAL_CONTROL_CENTER_DE.md)
- [PHASE0_RUNTIME_GATE.md](../../dev-dashboard/PHASE0_RUNTIME_GATE.md) (falls vorhanden)
