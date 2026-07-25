# Plan — Multi-Distro Linux-Install vom Rettungsstick + ASUS ROG Sofortpfad

**Stand:** 2026-07-25  
**Status:** Umsetzung gestartet (Contracts + Gates + Diagnose + UI/i18n; Execute = Handoff only)  
**Branch:** `cursor/asus-mint-multidistro-install-30f2`

## Distro-Matrix

| Profil | Status |
|--------|--------|
| `linux_mint` | **supported** (ASUS P0) |
| `ubuntu_server_lts` | planned |
| `ubuntu_server` | planned |
| `debian` | planned (Debian Live = Stick-Runtime) |

## Freigabe

Partitionshelfer-Write / Install-Handoff nur nach **Operator-Freigabe** *oder* **Backup+Verify**.

## ASUS Sofortpfad

- Keine Umsteck-Session  
- Mint auf zweiter NVMe  
- Orchestrierung: Dev-Laptop  
- Telemetrie/Diagnostik: private GitHub-Repos + IONOS (Fehlersuche)  
- `executed: false` bis physische Operator-Freigabe  

Siehe auch Implementierung:

- `backend/core/rescue_linux_distro_profiles_v1.py`
- `backend/core/rescue_linux_install_gate_v1.py`
- `backend/core/rescue_asus_mint_orchestration_v1.py`
- `GET/POST /api/rescue/linux-install/*`
