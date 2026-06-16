# MSI and Commercial Boundary — Monolith Audit

**Stand:** 2026-06-16 nach `1.8.12.0`  
**HEAD:** 94c91f1 (+ dieser Lauf)

## Größte Code-Dateien (ohne venv)

| Zeilen | Datei |
|--------|-------|
| 8829 | `backend/app.py` |
| ~3900+ | `backend/core/backup_execute_handlers.py` |
| ~970 | `backend/core/security_handlers.py` |
| ~440 | `backend/core/system_handlers.py` |

Vollständig: `docs/evidence/monolith/largest_files_after_1_8_12_0.txt`

## Nächste Monolith-Kandidaten (`app.py`)

| Bereich | Routen ca. | Entscheidung |
|---------|------------|--------------|
| `/api/users/*` | mehrere | `extract_later` (E.15+) |
| sudo-password | 2 | `extract_later` + Security-Review |
| `/api/raspberry-pi/config/*` | 6+ | `tests_first` |
| Webserver | 2+ | `extract_later` |
| NAS | 5+ | `extract_later` |
| Radio | 8+ | `extract_later` |
| Dev-Dashboard | viele | `wrap_with_facade` — lokal ≠ Operator-Dashboard |
| Helfer `_open_terminal_with_command` | — | `keep` in app.py (von system_handlers genutzt) |
| `_run_apt_*` | — | `keep` / bereits system_runtime |
| `get_updates_categorized` | — | `extract_later` → system_handlers |

## Duplikat-Risiken (Auszug)

| Thema | Datei A | Datei B | Überschneidung | Public/Private | Risiko | Entscheidung |
|-------|---------|---------|----------------|----------------|--------|--------------|
| Backup execute | `app.py` Helfer | `backup_execute_handlers.py` | Logik teilweise delegiert | public | mittel | `wrap_with_facade` |
| Security configure | `security_handlers.py` | `app.py` webserver preset | ähnliche UFW/Fail2ban-Pfade | public | niedrig | `extract_later` |
| Telemetry | `rescue_telemetry_client` | — | Client only | public-safe contract | niedrig | `public_safe_contract_only` |
| Cloud Edition | Handoff docs | — | keine Impl. | private_only | — | `private_only` |
| Windows/MSI | Plan-Docs | `windows_inspect` Schema | Inspect read-only | public | niedrig | `public_safe_contract_only` |
| Dev-Dashboard | `dev_dashboard_*` routes | Operator Handoff | Namensähnlichkeit | public vs private | mittel | `keep` + Doku trennen |

Scans: `msi_commercial_duplicate_scan_backend.txt`, `msi_commercial_keyword_scan.txt`

## Entscheidung Gesamt

- **Keine** Big-Bang-Refaktorierung
- **Keine** Löschung
- Nächster Code-Strang: Boundary + MSI Plan (dieser Lauf), dann Monolith E.15 (users) nach Operator-Priorität

## Inventar

`docs/evidence/monolith/repo_file_inventory_after_1_8_12_0.txt` — 5396 Dateien
