# DEVELOPER_DCC_USB_TOOLBOX_VISIBILITY_ROUTE_GATE_AND_VERSION_FIX

**Datum:** 2026-06-07  
**Version:** 1.7.3.1 → **1.7.4.0** (Funktionsänderung, 3. Stelle)

## Root Cause (live /opt)

| # | Ursache | Status |
|---|---------|--------|
| 1 | **Nicht deployed** — `rescue-usb/*` fehlt in `/opt` OpenAPI | **bestätigt** (HTTP 404) |
| 2 | Token-Datei fehlt | nein (`TOKEN_LEN=64`) |
| 3 | Browser-Token fehlt | möglich bis localStorage gesetzt |
| 4 | Header nicht mitgesendet | `fetchDccApi` korrekt; Fix: Compact-Shell auch bei `dcc_token_required` |
| 5 | Rescue-USB nicht in Allowlist | nein — Capability-Gate erlaubt `/api/dev-dashboard/*` mit Token |
| 6 | Frontend-Bundle alt | bis Deploy Frontend nach `/opt` |
| 7 | `/opt` nicht synchron | ja (HEAD-Features nur Workspace) |
| 8 | OpenAPI rescue-usb fehlt | ja auf Live-Runtime |

**Mit gültigem Token:** `capability-status` → `dcc_visible: true`, `DEVELOPER_CAPABILITY_VALID`  
**Ohne Token (Release):** `/api/dev-dashboard/status` → 404 `DEVELOPER_CAPABILITY_REQUIRED` (erwartet)  
**Telemetrie:** `/api/rescue/telemetry/health` → 200 (unabhängig)

## Fix (Workspace)

1. **Version 1.7.4.0** — `config/version.json`, sync-version → npm/Cargo/Tauri **1.7.4**
2. **Deploy-Verifikation** — Manifest + OpenAPI-Pflicht: `rescue-usb/candidates`, `rescue-usb/selection`
3. **DCC Frontend** — `dcc_token_required`: Compact-Cockpit + Token-Banner statt leerer Blockade
4. **Compact-Status** — immer laden; `rescue.usb_operator` angezeigt
5. **USB Toolbox** — Rescue-Tab, Capability-gated, kein dd

## Deploy (Operator)

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
./scripts/check-backend-version-gate.sh
python3 backend/tools/verify_deploy_to_opt.py --workspace /home/volker/piinstaller --runtime /opt/setuphelfer --phase all
```

Nach Deploy erwarten:

- `/api/version` → `project_version: 1.7.4.0`
- OpenAPI enthält `rescue-usb/*`
- Mit Token: `GET /api/dev-dashboard/rescue-usb/candidates` → **200**

## Tests

- `test_rescue_usb_operator_selection_v1.py`
- `test_deploy_runtime_verify_v1.py` (rescue-usb OpenAPI)
- `test_dev_dashboard_compact_status_v1.py`
- `dccBootState.test.ts`, `rescueUsbOperatorToolbox.test.ts`
- `npm run build`

## Commit / Push

- Commit: ja (selektiv)
- Push: nein

## Next Prompt

`RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT` (manueller dd nach Toolbox-Freigabe)
