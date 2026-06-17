# RS-P1 Initial Status

**Datum:** 2026-06-17  
**Lauf:** RS-P1 Rettungsstick Priorität 1

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD | `1266104` (vor RS-P1-Commit) |
| Workspace-Version | `1.9.5.0` (nach Funktionsänderung) |
| Runtime-Version | `1.9.2.0` (`/opt/setuphelfer`) |
| Runtime-Drift | ja — Workspace neuer als `/opt` |
| Drift-Bewertung | erwartet — Stick-Payload-Lauf ohne `/opt`-Deploy |
| Public/Private-Gate | Exit 0 |
| Module-Boundary-Gate | `review_required` (bekannt, Exit 0) |
| Dirty Tree | ja — RS-P1 Core/UI/Tests + unrelated DCC/private untracked |

```json
{
  "major_version_locked_to_1": true,
  "no_2_x_version": true,
  "rescue_stick_priority": true,
  "backup_execute_allowed": false,
  "restore_execute_allowed": false,
  "wipe_allowed": false
}
```
