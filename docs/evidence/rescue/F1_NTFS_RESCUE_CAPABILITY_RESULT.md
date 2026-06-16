# F.1 NTFS Rescue Capability — Result

**Datum:** 2026-06-16  
**Status:** **GREEN** (Detection Contract + Doku)

## Geliefert

- `windows_ntfs_detection_contract.py` — read-only, kein Bypass
- Rescue-Stick Capability Matrix + FAQ + KB
- API read-only: capabilities, precheck schema, parse-readonly
- 3 Router-Routen, keine Execute-Endpunkte

## Nicht geliefert (bewusst)

- NTFS mount/write auf MSI
- Image-Backup Execute (F.2)
- Rescue-ISO Paket-Rebuild in diesem Lauf

## Tests

`test_windows_ntfs_detection_contract_v1.py` — 10 passed  
`test_msi_windows_routes_readonly_v1.py` — 5 passed
