> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/NETWORK_NEXT_FACADE_CANDIDATES_G5_EN.md`). Bitte bei Release manuell gegenlesen.

# Network Next Fassade Candidates — G.5 (EN)

**HEAD:** `307c411` · **Stand:** Audit only — no implementation

## Candidates

### 1. System Info Fassade (G.6) — **HIGH**

- **Proposed path:** `backend/core/system_info_facade.py`
- **Scope:** `GET /api/system-info` aggregation (psutil, hardware, sensors, OS)
- **Network:** `network` block keeps delegating to `network_info_facade`
- **Why:** Largest remaining monolith GET (~240 lines); 4 frontend consumers; G.4 documented as blocked

### 2. Webserver Stand Fassade (G.7) — **HIGH**

- **Proposed path:** `backend/core/webserver_status_facade.py`
- **Scope:** `GET /api/webserver/status` payload
- **Why:** G.4 blocked due to `run_command`/`systemctl`; direct `_detect_frontend_port` bypass

### 3. Frontend Runtime Fassade — **MEDIUM**

- **Proposed path:** `backend/core/frontend_runtime_facade.py`
- **Scope:** Frontend port detection (5173/3001/3002)
- **Why:** Cross-cutting for `system/network` and `webserver/status`

### 4. Port Detection Fassade — **LOW** (standalone) / **MEDIUM** (inside Frontend Runtime)

- **Recommendation:** Merge into Frontend Runtime Fassade

### 5. Network Discovery Core (optional G.8) — **CRITICAL** (legacy elimination)

- **Proposed path:** `backend/core/network_discovery.py`
- **Scope:** `get_network_info` implementation (ip/hostname)
- **Why:** Breaks `facade → import app` cycle without HTTP changes

## Priority matrix

| Candidate | Priority | Legacy elimination | Router-ready |
|-----------|----------|-------------------|--------------|
| Network Discovery (G.8) | CRITICAL | high | no (internal) |
| System Info (G.6) | HIGH | medium | yes |
| Webserver Stand (G.7) | HIGH | medium | yes |
| Frontend Runtime | MEDIUM | medium | partial |
| Port Detection alone | LOW | low | no |

## Recommended decision

| Option | When |
|--------|------|
| **G.6** | Monolith reduction, dashboard polling, largest handler |
| **G.7** | Close network legacy bypass (`_detect_frontend_port`), smaller scope |
| **G.8** | Pure legacy elimination without new HTTP facade |
| **New architecture track** | Umbrella “Platform Runtime Fassade” if system + webserver should be owned together |

**Audit recommendation:** **G.8** or **G.7** first (smaller scope, closes direct bypass). **G.6** next as largest slice.

No API, route, or response changes in G.5.
