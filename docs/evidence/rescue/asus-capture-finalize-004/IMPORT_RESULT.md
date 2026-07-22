# Import-Ergebnis — PI-RS-ASUS-CAPTURE-FINALIZE-004

## Auswahl (manuell, identity-gated)

| Feld | Wert |
|------|------|
| Run | `hw-discovery-20260723T000800Z-e2c6903a` |
| Boot | `4e13e0d7-5fd4-4ef7-88cb-44d46aac8720` |
| Profil | `asus_rog_gabriel` |
| Payload | `1.10.2.1` |
| Status | `partial` terminal=`True` |
| Endstatus | `diagnosis_incomplete` |
| GUI | `not_applicable_for_text_hardware_discovery` |
| Marker | PARTIAL.TAG |
| Manifest/SHA256 | ja |

## Ausgeschlossen

- nichtterminaler Alt-Lauf `0ec17061`
- älterer Partial-Lauf `ec71f2a6` (gleicher Abend, nicht der letzte)
- MSI-Pfad `msi-rs011b` auf dem Stick
- kein newest-session Fallback
- `protected_raw` nicht importiert

## Befund

- Gerätebindung + BIOS + NVMe-Identität: complete (2× Samsung 970 EVO Plus 2TB, EUI ja, NGUID nein)
- SMART / Error-Logs / Kernel / Partitionen / Panther: **fehlen** (`capture_exception:ValueError`)
- Finalizer: **erreicht** (terminal partial)

## Diagnose-Status

`diagnosis_incomplete`
