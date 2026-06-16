# Kampagne A.3 — G.13 + P.2 + D.13 (Vorbereitung)

**Nach:** A.1 Commit `8940213` · Version `1.7.14.0`  
**Datum:** 2026-06-10

## Harte Regeln (unverändert)

- Kein Deploy / Backup / Restore / Rescue Build / USB Write / Hardwaretest
- Kein Runtime-Smoke / systemctl / sudo / apt / npm install
- Kein `git add -A`
- Keine API-/Response-/OpenAPI-/UI-Änderungen
- MODULE_CATALOG + Ownership + Do-Not-Duplicate + Roadmap vor jeder Phase

---

## G.13 — System Status Facade ohne `import app`

### Ist (nach A.1)

`system_status_facade.py` delegiert Ampel an `system_status_core`, aber:

| Section | Problem |
|---------|---------|
| `build_backend_runtime_section` | `import app` → `get_pi_installer_version`, `get_app_edition` |
| `build_installation_section` | `import app` → `OPT_INSTALL_DIR`, `_read_version_from_path` |
| `build_profile_section` | `import app` → `_user_profile_collect_from_disk`, `UserProfile` |

### Ziel

Neue Core-Owner (oder Erweiterung `system_status_core` / dedizierte Hilfsmodule):

- `build_backend_runtime_status()` — Version/Edition/Runtime-Pfad ohne Facade→app
- `build_installation_status()` — /opt-Drift read-only
- `build_profile_status()` — Profil von Disk read-only

Facade: nur Delegation, kein `import app`.

### Evidence

`docs/evidence/app-monolith/SYSTEM_STATUS_FACADE_APP_IMPORT_AUDIT_G13.md`

---

## P.2 — `app.py` Storage-Migration

### Ziel-Blöcke (read-only)

| Symbol | Zeilen (ca.) | Canonical API |
|--------|--------------|---------------|
| `_lsblk_tree` | ~10848+ | `storage_discovery.discover_block_devices` |
| `_findmnt_mounts` | ~11190+ | `storage_discovery.discover_mounts` |
| blkid-Helfer | ~11683+ | `storage_discovery.discover_filesystems` |

### Regeln

- Nur sichere read-only Migrationen
- Keine Schreiboperationen / Mount-Execute
- Bei Risiko: markieren, dokumentieren, nicht umbauen

### Evidence

`docs/evidence/storage/APP_STORAGE_MIGRATION_AUDIT_P2.md`  
Update: `STORAGE_DISCOVERY_OWNERSHIP_MATRIX.md`

---

## D.13 — Rescue-Domain-Router

### Ist

`deploy/routes.py`: **99** rescue-Routen inline, **81** Runner-Imports.

### Ziel

1. Vollständiges Audit + Klassifikation (plan / readonly / execute / write)
2. Extraktion **nur** plan-only + readonly Slice → `routes_rescue.py` (oder Subrouter)
3. **Keine** Execute-/Write-Routen anfassen

### Evidence

`docs/evidence/deploy-runner/RESCUE_DOMAIN_ROUTER_AUDIT_D13.md`  
`docs/architecture/RESCUE_DOMAIN_ROUTER_SLICE_PLAN_D13.md`

---

## Phase 0 Gates (Pflicht)

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
./scripts/check-module-boundaries.sh || true
./scripts/check-runtime-deploy-gate.sh || true
```

## Nächste Version (bei Umsetzung)

Funktionsänderung → 3. Stelle: `1.7.14.0` → `1.7.15.0`  
oder Patch-only-Docs: 4. Stelle `1.7.14.1`
