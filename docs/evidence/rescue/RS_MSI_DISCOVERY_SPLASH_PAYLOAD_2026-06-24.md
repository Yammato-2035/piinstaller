# RS MSI Discovery + Splash Payload — 2026-06-24

## Phase 0 — Stand

| Feld | Wert |
|------|------|
| Commit (Fix) | `2cfb8da` — `fix(rescue): improve MSI backup source discovery and boot splash` |
| Version (Payload) | `1.9.16.2` |
| Runtime-Gate | Exit 0 (Profil-Hinweis dev-dashboard 404 erwartet) |
| Dev-Host | volker — kein GE63-Live-Boot in dieser Session |

## Phase 2 — Tests

```bash
python3 -m pytest backend/tests/test_rescue_windows_backup_discovery_v1.py \
  backend/tests/test_rescue_ui_api_proxy_v1.py backend/tests/test_rescue_p3v3_contract_v1.py -q
# 7 passed

backend/venv/bin/pip-audit -r backend/requirements.txt
# No known vulnerabilities found

cd frontend && npm audit --omit=dev --audit-level=high
# found 0 vulnerabilities (high)
```

## Phase 3 — Payload

| Feld | Wert |
|------|------|
| Quelle SquashFS | `build/rescue/filesystem.squashfs.repacked-1.9.16.1` |
| Neu | `build/rescue/filesystem.squashfs.repacked-1.9.16.2` |
| SHA256 | `fc8cac9d8a7600c7b927ff54936b80c18f67e9a8b78b17704de8863b740ed413` |
| Manifest | `build/rescue/rescue-build-manifest.json` |
| Skript | `scripts/rescue-live/repack-rescue-squashfs-react-shell.sh` |

### Enthaltene Fixes

- Windows-Gruppierung + Auto-Selection (`rescue_storage_discovery.py`, `RescueBackupPanel.tsx`)
- Boot-Splash ohne Konsolen-Rauschen (`setuphelfer-rescue-x11-hold`, `gui-watchdog`, `RescueBootSplash.tsx`)
- Plan-Contract: explizite `source_role` (`rescue_disk_role_classifier.py`)

## Phase 4 — Stick-Integration

| Prüfung | Ergebnis |
|---------|----------|
| Stick | `/dev/sda` (59G, USB, RM) |
| SETUPHELFER | `/dev/sda1` (4G) — gemountet für Payload |
| SETUP_LOGS | `/dev/sda2` (55G) — `/media/volker/SETUP_LOGS` |
| Partition rewrite | **nein** |
| mkfs/dd | **nein** |
| Alter Stick-SHA | `64b6bc137fcae65d089126b5533a929aaae480e05f0c08a70d0b44963c7c96bd` |
| Neuer Stick-SHA | `fc8cac9d8a7600c7b927ff54936b80c18f67e9a8b78b17704de8863b740ed413` ✓ |
| Verify | **success** |
| Evidence | `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_20260624_203716/` |

## Phase 5 — MSI Live-Test Checkliste (Operator)

1. **GE63 vom Rettungsstick booten** (`/dev/sda` am MSI — **nicht** am Dev-Host `/dev/sdb` annehmen)
2. **Splash:** sauber, keine Steuerzeichen, GUI startet
3. **Externe USB-HDD** anschließen
4. **Live prüfen** (lsblk/Discovery — **kein** festes `/dev/sdb`):
   - Gerät wirklich extern?
   - Nicht Rettungsstick?
   - Nicht internes NVMe?
   - ext4 gemountet?
   - Freier Speicher ≥ Quelle + 5%?
5. **Discovery:** Windows-System auto → `/dev/nvme0n1`, EFI+Windows+Recovery gruppiert
6. **Backup-Plan:** `source`/`target`/`plan_status` = **ready** (nur wenn Mount + Kapazität OK)
7. **Backup starten** erst nach expliziter Freigabe: *„MSI BACKUP AUF EXTERNE HDD FREIGEGEBEN“*

## Phase 6 — Backup-Freigabe

**Kein Backup in dieser Session ausgeführt.**

## Status

**GELB** — Payload auf Dev-Stick `sda` verifiziert; MSI GE63 Live-Boot + Discovery/Plan-GRÜN ausstehend.
