# PI-RS-INSTALL-ASSISTANT-001 — Zug A3 Partition Dry-Run

## Ziel

Partitionsplan grün ohne Schreiben; Anbindung an Partitionshelfer-Preview (`write_allowed: false`).

## Verhalten

- `build_linux_partition_plan()` liefert `plan_hash`, Layout EFI/root/home
- `windows_nvme_write_allowed: false`, `partitionshelfer_write_allowed: false`
- Windows-Rolle als Mint-Ziel → `blocked` / `windows_role_forbidden_as_mint_target` (Extra-Gate-Flag nötig, Execute weiter false)
- Execute-Endpoint liefert hart `executed: false` + Handoff-Hinweis

## UI

Plan anzeigen; Doppelbestätigung disabled bis A5.
