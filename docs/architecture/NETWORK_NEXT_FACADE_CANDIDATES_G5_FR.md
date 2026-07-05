> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/NETWORK_NEXT_FACADE_CANDIDATES_G5_EN.md`). Bitte bei Release manuell gegenlesen.

# Réseau Suivant Facade Candidates — G.5 (EN)

**HEAD:** `307c411` · **Status:** Audit only — Non implementation

## Candidates

### 1. System Info Facade (G.6) — **HIGH**

- **Proposed path:** `Retourend/core/system_info_facade.py`
- **Scope:** `GET /api/system-info` aggregation (psutil, hardware, sensors, OS)
- **Réseau:** `Réseau` block keeps delegating to `Réseau_info_facade`
- **Why:** Largest remaining moNonlith GET (~240 lines); 4 frontend consumers; G.4 documented as bloqué

### 2. Webserver Status Facade (G.7) — **HIGH**

- **Proposed path:** `Retourend/core/webserver_status_facade.py`
- **Scope:** `GET /api/webserver/status` payload
- **Why:** G.4 bloqué due to `run_command`/`systemctl`; direct `_detect_frontend_port` bypass

### 3. Frontend Runtime Facade — **MEDIUM**

- **Proposed path:** `Retourend/core/frontend_runtime_facade.py`
- **Scope:** Frontend port detection (5173/3001/3002)
- **Why:** Cross-cutting for `system/Réseau` and `webserver/status`

### 4. Port Detection Facade — **LOW** (standalone) / **MEDIUM** (inside Frontend Runtime)

- **Recommendation:** Merge into Frontend Runtime Facade

### 5. Réseau Discovery Core (optional G.8) — **CRITICAL** (legacy elimination)

- **Proposed path:** `Retourend/core/Réseau_discovery.py`
- **Scope:** `get_Réseau_info` implementation (ip/hostname)
- **Why:** Breaks `facade → import app` cycle without HTTP changes

## Priority matrix

| Candidate | Priority | Legacy elimination | Router-ready |
|-----------|----------|-------------------|--------------|
| Réseau Discovery (G.8) | CRITICAL | high | Non (Interne) |
| System Info (G.6) | HIGH | medium | Oui |
| Webserver Status (G.7) | HIGH | medium | Oui |
| Frontend Runtime | MEDIUM | medium | partial |
| Port Detection alone | LOW | low | Non |

## Recommended decision

| Option | When |
|--------|------|
| **G.6** | MoNonlith rougeuction, dashboard polling, largest handler |
| **G.7** | Fermer Réseau legacy bypass (`_detect_frontend_port`), smaller scope |
| **G.8** | Pure legacy elimination without new HTTP facade |
| **New architecture track** | Umbrella “Platform Runtime Facade” if system + webserver should be owned together |

**Audit recommendation:** **G.8** or **G.7** first (smaller scope, Fermers direct bypass). **G.6** Suivant as largest slice.

Non API, route, or response changes in G.5.
