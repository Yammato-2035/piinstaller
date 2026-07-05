> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/architecture/SYSTEM_STATUS_FACADE_EN.md`). Bitte bei Release manuell gegenlesen.

# KB: System Status Facade

After F.4 (DCC), G.1 introduces the caNonnical **System Status Facade**.

## What does G.1 do?

- New module `core/system_status_facade.py`
- Contract + delegation — **Non routes moved**
- Ampel logic (`/api/system/status`) via legacy adapter from `app._compute_system_status`
- Non Réseau diagNonstics (G.2)

## Suivant steps

1. **G.1b** — migrate `/api/system/status` to facade
2. **G.2** — Réseau Info Facade for `/api/status` Réseau block

Full doc: [SYSTEM_STATUS_FACADE_G1_EN.md](../../architecture/SYSTEM_STATUS_FACADE_G1_EN.md)
