# KB: System Status Facade

After F.4 (DCC), G.1 introduces the canonical **System Status Facade**.

## What does G.1 do?

- New module `core/system_status_facade.py`
- Contract + delegation — **no routes moved**
- Ampel logic (`/api/system/status`) via legacy adapter from `app._compute_system_status`
- No network diagnostics (G.2)

## Next steps

1. **G.1b** — migrate `/api/system/status` to facade
2. **G.2** — Network Info Facade for `/api/status` network block

Full doc: [SYSTEM_STATUS_FACADE_G1_EN.md](../../architecture/SYSTEM_STATUS_FACADE_G1_EN.md)
