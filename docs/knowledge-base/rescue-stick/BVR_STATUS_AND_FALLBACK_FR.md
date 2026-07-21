# Statut BVR et repli GUI (KB)

**Task:** PI-RS-BVR-GUI-DCC-001

## Statuts globaux

| Statut | Signification |
|--------|---------------|
| `passed` | BVR + GUI visible |
| `passed_with_gui_fallback` | BVR reussi, GUI non visible / repli |
| `failed` | Noyau BVR en echec |
| `implemented_pending_physical_retest` | Correctif code, pas de run MSI confirme |
| `review_required` | Evaluation manuelle requise |

## Baseline (reference)

Run `e2e-rescue-msi-20260721-232222-ba58c7a7`, payload `1.10.1.0` :

- BVR : **passed**
- GUI : **non visible** (`http_server_failed`)
- Global : **`passed_with_gui_fallback`**

## Regle

Evaluer le noyau BVR et la GUI **separement**. L'echec GUI ne bloque pas backup/verify/restore.

## Voir aussi

- [GUI_WATCHDOG_FALLBACK.md](../../rescue-stick/GUI_WATCHDOG_FALLBACK.md)
