> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/NETWORK_NEXT_FACADE_CANDIDATES_G5_EN.md`). Bitte bei Release manuell gegenlesen.

# Netwerk Volgende Facade Candidates — G.5 (EN)

**HEAD:** `307c411` · **Status:** Audit only — Nee implementation

## Candidates

### 1. System Info Facade (G.6) — **HIGH**

- **Proposed path:** `Terugend/core/system_info_facade.py`
- **Scope:** `GET /api/system-info` aggregation (psutil, hardware, sensors, OS)
- **Netwerk:** `Netwerk` block keeps delegating to `Netwerk_info_facade`
- **Why:** Largest remaining moNeelith GET (~240 lines); 4 frontend consumers; G.4 documented as geblokkeerd

### 2. Webserver Status Facade (G.7) — **HIGH**

- **Proposed path:** `Terugend/core/webserver_status_facade.py`
- **Scope:** `GET /api/webserver/status` payload
- **Why:** G.4 geblokkeerd due to `run_command`/`systemctl`; direct `_detect_frontend_port` bypass

### 3. Frontend Runtime Facade — **MEDIUM**

- **Proposed path:** `Terugend/core/frontend_runtime_facade.py`
- **Scope:** Frontend port detection (5173/3001/3002)
- **Why:** Cross-cutting for `system/Netwerk` and `webserver/status`

### 4. Port Detection Facade — **LOW** (standalone) / **MEDIUM** (inside Frontend Runtime)

- **Recommendation:** Merge into Frontend Runtime Facade

### 5. Netwerk Discovery Core (optional G.8) — **CRITICAL** (legacy elimination)

- **Proposed path:** `Terugend/core/Netwerk_discovery.py`
- **Scope:** `get_Netwerk_info` implementation (ip/hostname)
- **Why:** Breaks `facade → import app` cycle without HTTP changes

## Priority matrix

| Candidate | Priority | Legacy elimination | Router-ready |
|-----------|----------|-------------------|--------------|
| Netwerk Discovery (G.8) | CRITICAL | high | Nee (Intern) |
| System Info (G.6) | HIGH | medium | Ja |
| Webserver Status (G.7) | HIGH | medium | Ja |
| Frontend Runtime | MEDIUM | medium | partial |
| Port Detection alone | LOW | low | Nee |

## Recommended decision

| Option | When |
|--------|------|
| **G.6** | MoNeelith rooduction, dashboard polling, largest handler |
| **G.7** | Sluiten Netwerk legacy bypass (`_detect_frontend_port`), smaller scope |
| **G.8** | Pure legacy elimination without new HTTP facade |
| **New architecture track** | Umbrella “Platform Runtime Facade” if system + webserver should be owned together |

**Audit recommendation:** **G.8** or **G.7** first (smaller scope, Sluitens direct bypass). **G.6** Volgende as largest slice.

Nee API, route, or response changes in G.5.
