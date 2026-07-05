> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/knowledge-base/architecture/SYSTEM_STATUS_FACADE_EN.md`). Bitte bei Release manuell gegenlesen.

# KB: System Status Facade

After F.4 (DCC), G.1 introduces the caNeenical **System Status Facade**.

## What does G.1 do?

- New module `core/system_status_facade.py`
- Contract + delegation — **Nee routes moved**
- Ampel logic (`/api/system/status`) via legacy adapter from `app._compute_system_status`
- Nee Netwerk diagNeestics (G.2)

## Volgende steps

1. **G.1b** — migrate `/api/system/status` to facade
2. **G.2** — Netwerk Info Facade for `/api/status` Netwerk block

Full doc: [SYSTEM_STATUS_FACADE_G1_EN.md](../../architecture/SYSTEM_STATUS_FACADE_G1_EN.md)
