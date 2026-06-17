# RS-F2B.1 Initial Status

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD | `00bb2a4` (vor RS-F2B.1 Änderungen, dirty tree) |
| Workspace-Version | `1.9.4.0` |
| Runtime-Version | `1.9.2.0` (`/opt/setuphelfer`) |
| Public/Private-Gate | **0** (ok) |
| Module-Boundary-Gate | review_required (Warnings, kein Block) |
| Runtime-Gate | Drift workspace 1.9.4.0 vs API 1.9.2.0 |
| Dirty Tree | ja (RS-F2S + RS-F2B.1 uncommitted) |
| Bekannter Stick-SHA256 (vor Update) | Squashfs `1992d67c66df41223d623d4f06fc44bcad054ec95734385044549a0a0b9caf57` |
| Neuer Squashfs-SHA256 (nach Update) | `3cbfca25997ce549b38e6ab640f63ae0a4a77f2ce66891811f97e78467480f61` |
| Stick-Gerät | `/dev/sda` Intenso Ultra Line 59G |

## MSI-Boot-Ergebnis (RS-F2S)

| Feld | Wert |
|------|------|
| wlan_not_found | true (UI: kein Scan/Connect) |
| local_telemetry_expected | true |
| backup_plan_created | false (`disk_discovery: null`, `action_plan: null`) |

## Safety

- Kein MSI-Backup, Restore, Verify Deep, Wipe, Format, NTFS-Schreiben.
- Public/Private-Gate grün — Build fortgesetzt.
