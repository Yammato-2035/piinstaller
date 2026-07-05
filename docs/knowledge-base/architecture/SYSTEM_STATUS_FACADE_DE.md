> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/knowledge-base/architecture/SYSTEM_STATUS_FACADE_EN.md`). Bitte bei Release manuell gegenlesen.

# KB: System Stand Fassade

After F.4 (DCC), G.1 introduces the canonical **System Stand Fassade**.

## What does G.1 do?

- New module `core/system_status_facade.py`
- Contract + delegation — **no routes moved**
- Ampel logic (`/api/system/status`) via legacy adapter from `app._compute_system_status`
- No network diagnostics (G.2)

## Next steps

1. **G.1b** — migrate `/api/system/status` to facade
2. **G.2** — Network Info Fassade for `/api/status` network block

Full doc: [SYSTEM_STATUS_FACADE_G1_EN.md](../../architecture/SYSTEM_STATUS_FACADE_G1_EN.md)
