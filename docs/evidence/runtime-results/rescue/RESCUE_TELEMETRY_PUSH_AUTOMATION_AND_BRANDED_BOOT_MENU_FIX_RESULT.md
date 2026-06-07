# RESCUE_TELEMETRY_PUSH_AUTOMATION_AND_BRANDED_BOOT_MENU_FIX — Ergebnis

**Datum:** 2026-06-07  
**Workspace HEAD (vorher):** `f52dab3`  
**Version (vorher → nachher):** `1.7.5.0` → **`1.7.6.0`**

## Phase 0 — Ist-Zustand

| Prüfung | Ergebnis |
|---------|----------|
| Branch | `main` |
| Workspace-Version | `1.7.6.0` (nach Fix) |
| API `/api/rescue/telemetry/health` | HTTP 200, `status=ok` |
| LAN-Proxy `:8001` | HTTP 200, `status=ok` |
| API-Drift | Workspace `1.7.6.0` vs Runtime API `1.7.4.1` (dokumentiert, kein Build-Blocker) |
| `last_ingest_at` | `null` |
| `last_ack_id` | `null` |
| `last_error_code` | `TELEMETRY-SCHEMA-001` (historisch, kein Proxy-Fehler) |

## Phase 1 — Root Cause SyntaxError

**Datei:** `scripts/rescue-live/image/setuphelfer-rescue-telemetry-push` (generiertes Inline-Python via Bash-Heredoc)

**Ursache:** `json.loads("""$(echo "$_lsblk" | python3 -c 'json.dumps(...)')""")` — wenn `json.dumps()` mit `"` beginnt, entsteht neben dem Python-Triple-Quote `"""` ein vierter `"` → `""""` → **`SyntaxError: unterminated string literal (detected at line 31)`** (Python-Zeile der `lsblk`-Einbettung).

**Reproduktion (lokal):** Ausführung des alten Scripts mit echtem `lsblk -J` auf dem Host → identischer Fehler.

**Fix:** Separates Python-Modul `setuphelfer-rescue-telemetry-build-payload.py`; Shell-Wrapper ohne Inline-Heredoc-JSON.

## Phase 2–4 — Telemetrie / Boot-Automatisierung / WLAN-Config

| Komponente | Status |
|------------|--------|
| `setuphelfer-rescue-telemetry-build-payload.py` | neu, `py_compile` OK |
| `setuphelfer-rescue-telemetry-push` | Health 10s / Ingest 20s, Spool, Exit-Codes 0/10/11/12/13/20/30 |
| `setuphelfer-rescue-telemetry-retry` + `.timer` | Spool-Retry alle 5 min |
| `setuphelfer-rescue-network-onboarding` | Auto-Scan, known NM profile, `network.env`, PSK-Datei, whiptail-Fallback |
| `setuphelfer-rescue-common.sh` | Config-Discovery unter `/run`, `/etc`, `/media/*/SETUPHELFER_*_CONFIG/` |
| systemd | Onboarding → Telemetry-Push → Task-Pull; Retry-Timer enabled |

**Keine Secrets im Repo.** Beispiel: `etc/setuphelfer-rescue/network.env.example`.

## Phase 5 — Boot-Menü / Branding

| Element | Status |
|---------|--------|
| `setuphelfer-rescue-boot-branding.txt` | ASCII-Logo in `/usr/share/setuphelfer/rescue/` |
| ISOLINUX `020-setuphelfer-rescue-boot-menu.hook.binary` | 7 Einträge inkl. MSI-Kompat, Diagnose, toram, Reboot, Poweroff |
| GRUB `patch_grub` | gleiche Einträge für `binary/boot/grub/grub.cfg` |
| `isolinux.cfg` MENU TITLE | `write_rescue_isolinux_branding()` (Standard-Profil) |

## Phase 6 — Tests

```
python3 -m unittest backend.tests.test_rescue_live_telemetry_scripts_v1 ...  OK (7)
python3 -m unittest backend.tests.test_rescue_telemetry_boot_network_v1 ... OK (3)
python3 -m unittest backend.tests.test_rescue_network_telemetry_gate_v1 ... OK (3)
npm run build ... OK
bash -n scripts/rescue-live/prepare-controlled-live-build-tree.sh ... OK
bash -n scripts/rescue-live/validate-controlled-live-build-tree.sh ... OK
```

## Phase 7 — Prepare / Validate

| Schritt | Ergebnis |
|---------|----------|
| `prepare-controlled-live-build-tree.sh` | **OK** |
| `validate-controlled-live-build-tree.sh` | **BLOCKIERT** — root-owned `chroot/` + `FORBIDDEN: chroot/usr/lib/firmware/RTL8192E/main.img` (stale lb-Artefakte) |

**Operator-Clean erforderlich:**

```bash
cd /home/volker/piinstaller
sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live
```

## Phase 8 — ISO-Rebuild

**Nicht durchgeführt** (Validate nicht grün wegen stale root-owned chroot).

Nach Operator-Clean + Validate grün:

```bash
export RESCUE_NETWORK_AUTOMATION_REBUILD_FREIGEGEBEN=1
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

## Gates (ehrlich)

| Gate | Wert |
|------|------|
| `telemetry_push_syntax_fixed` | **true** (workspace + py_compile) |
| `boot_automation_prepared` | **true** (systemd units im Build-Tree) |
| `boot_menu_branding_prepared` | **true** (Hook + Branding-Datei) |
| `iso_rebuilt` | **false** |
| `target_telemetry_ingest_ack` | **false** (MSI-Retest ausstehend) |
| `usb_write_sha256_verified` | **false** |
| `windows_inspect_executable` | **false** |

## Nächster Prompt

**`RESCUE_TELEMETRY_AUTOMATION_ISO_REBUILD_OPERATOR_COMPLETION`**

Danach: **`RESCUE_USB_REWRITE_OPERATOR_AFTER_TELEMETRY_AUTOMATION_FIX`** → **`RESCUE_MSI_BOOT_AUTOMATED_TELEMETRY_ACK_OPERATOR_RUN`**
