# Partitionshelfer – Phase 1 (read-only)

## Überblick

- **Ziel-UI:** React/Tauri im Setuphelfer-Frontend (`frontend/src/pages/PartitionManager.tsx`)
- **API:** `/api/partitions/*` (`backend/api/routes/partitions.py`)
- **Logik:** `apps/partitionshelfer/core/` (Scan + Safety, Import über `setuphelfer_partitions_core`)
- **Fallback:** tkinter (`apps/partitionshelfer/start.py`) – bleibt bestehen

## Phase 1 – Grenzen

- Nur **lesen**: Scan, Safety-Analyse, geführte Wizards (Anleitung).
- Schreib-Buttons in der UI: sichtbar, **deaktiviert** (`partition.actions.comingSoon`).
- `POST /api/partitions/queue/apply`: **Stub** – keine `mkfs`/`parted`/`dd`-Ausführung.

## Phase 2 (geplant)

Schreibaktionen erst nach Hardstop-/SMART-/Manifest-Layout-Gates und expliziter Operator-Freigabe (align mit BR-001 und `validate_write_target()`).

## Rettungsstick / Produktkontext

Für Setuphelfer am Rettungsstick und am Desktop wird die **Web/Tauri-Oberfläche** bevorzugt; tkinter dient als Offline-Fallback ohne Netzwerk-Backend.

## Runtime / Deploy

Produktives Backend: `/opt/setuphelfer/backend`. Nach Workspace-Änderungen:

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
sudo systemctl restart setuphelfer-backend.service
```

Evidence: `docs/evidence/partitions/PARTITIONS_PHASE1_RUNTIME_VALIDATION.md`
