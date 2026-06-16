# Rettungsstick Status Audit R.2

**Kampagne:** B.1 · **Version:** 1.7.15.0 · **Datum:** 2026-06-10  
**Modus:** Read-only Audit (kein Runtime-Smoke, kein HW-Test)

---

## Zusammenfassung

| Bereich | Ampel | Kurzurteil |
|---------|-------|------------|
| Boot-Pfad (live-build → GRUB/ISOLINUX) | 🟡 | Architektur und QEMU solide; HW-Level-6 und GRUB-Theme auf ESP ausstehend |
| Deploy Rescue-Routen | 🟡 | 84 POST in `routes.py` + 25 plan-only in Subroutern; ~12 Execute-Endpunkte |
| Rescue API-Router (Telemetry/Agent/Remote) | 🟡 | Drei getrennte Router; R.2-Konsolidierung offen |
| Bekannte Fehler (Evidence) | 🟡 | Viele Fixes im Workspace; Release-/HW-Gates blockieren Grün |
| WLAN | 🟡 | TUI funktional; React-UI und MSI-Retest offen |
| Telemetrie | 🟡 | SyntaxError-Crash behoben; HW-Ingest nicht nachgewiesen |
| Netzwerkscan | 🟡/🔴 | TUI ja (`nmcli`); React/API-Shell nein |
| Grafische Assets | 🟢/🟡 | Workspace vollständig; End-to-End auf HW pending |
| Recovery-Menü | 🟡 | TUI plan-only nutzbar; React Shell rein visuell |

**Gesamtreife Rettungsstick:** 🟡 **Gelb** — produktionsnah im Lab, nicht HW-abgenommen.

---

## 1. Aktueller Bootpfad

```
UEFI/BIOS
  → GRUB (UEFI) / ISOLINUX (BIOS)
  → vmlinuz + initrd (setuphelfer_rescue=1)
  → systemd live
  → setuphelfer-rescue-start-assistant (--boot-trigger)
      → React-UI-Launch (setuphelfer-rescue-ui-launch)
          → Fallback: whiptail TUI
      → Wizard: welcome → media → network → telemetry → disks → recommendation → main_menu
```

### Artefakte

| Stufe | Pfad / Skript | Status |
|-------|---------------|--------|
| Live-build Tree | `build/rescue/live-build/setuphelfer-rescue-live/` | 🟡 Validator/QEMU ok, HW-E2E offen |
| Prepare/Validate | `scripts/rescue-live/prepare-controlled-live-build-tree.sh`, `validate-*` | 🟢 |
| ISOLINUX / BIOS | `scripts/rescue-live/image/setuphelfer-rescue-boot-menu-snippet.cfg` | 🟢 (KB-012) |
| GRUB / UEFI | `scripts/rescue-live/image/setuphelfer-rescue-grub-menu-snippet.cfg` | 🟡 Theme auf ESP HW-Retest pending |
| Splash / Branding | `assets/rescue/splash/setuphelfer-splash.png` | 🟢 ISO-Ebene |
| Grafische Assets Staging | `scripts/rescue-live/stage-rescue-graphical-assets.sh` | 🟢 |
| Boot-Trigger | Kernel-Cmdline `setuphelfer_start_assistant=1` | 🟡 |
| React Shell | `frontend/src/rescue/RescueApp.tsx` → SquashFS | 🔴 Kein Browser/Kiosk im Live-OS |

**Evidence:** `RESCUE_STICK_IST_ANALYSIS.md`, `RS_001_GRUB_BRANDING_ANALYSIS.md`, `RS_001_REACT_UI_LAUNCHER_ANALYSIS.md`, `CONTROLLED_ISO_BUILD_BOOT_MENU_BRANDING_REVIEW.md`

---

## 2. Offene Execute-Routen

### Deploy (`backend/deploy/routes.py`)

| Klasse | Anzahl | Modul |
|--------|--------|-------|
| Rescue POST gesamt in `routes.py` | **84** | Mix plan/gate/execute |
| Rescue plan-only (Subrouter) | **25** | `routes_rescue_readonly.py` (4) + `routes_rescue_plan.py` (21) |
| Rescue-stick POST | **10** | `routes.py` |

**Execute-fähige Endpunkte (Auswahl):**

| Route | Risiko |
|-------|--------|
| `POST /rescue/iso-build-execute` | ISO-Build |
| `POST /rescue/vm-test-execute` | QEMU-Validierung |
| `POST /rescue/sandbox-copy/config` | Sandbox-Write |
| `POST /rescue/sandbox-copy/runtime` | Sandbox-Write |
| `POST /rescue/storage-discovery` (`act=execute`) | Laufwerksprobe |
| `POST /rescue/readonly-mount-validation` | Mount-Validierung |
| `POST /rescue/evidence-export` | Evidence-Export |
| `POST /rescue/restore-preview` (`act=execute`) | Restore-Preview |
| `POST /rescue/backup-discovery-verify` | Backup-Discovery |

Gates: `explicit_overwrite`, `explicit_execute_*`, `act=="execute"` — vorhanden, aber Monolith `routes.py` noch ~3.704 Zeilen.

### Rescue API-Router (nicht deploy)

| Router | Prefix | Endpunkte | Profil |
|--------|--------|-----------|--------|
| `rescue_telemetry/routers.py` | `/api/rescue/telemetry` | 5 | Release-tauglich |
| `rescue_agent/routers.py` | `/api/rescue-agent` | 6 | Stub, non-release |
| `rescue_remote/routers.py` | `/api/rescue-remote` | 9 | `rescue_remote_enabled` |

**Gap R.2:** Drei getrennte Ingest-/Agent-Router — Konsolidierung in Architektur-Roadmap offen.

**Evidence:** `DEPLOY_RESCUE_DOMAIN_AUDIT_D13.md`, `RESCUE_DOMAIN_BATCH2_D14.md`

---

## 3. Bekannte Fehler

| Issue | Status | Referenz |
|-------|--------|----------|
| Telemetrie `SyntaxError` (Inline-Heredoc) | ✅ Behoben ab 1.7.6.0 | KB-011 |
| Boot-Menü fehlte in ISO | ✅ Behoben ab 1.7.7.0 | KB-012 |
| WLAN-Menü bricht ab | ✅ Behoben ab 1.7.7.0 | KB-013 |
| dpkg/start-stop-daemon live-build | ✅ Preflight-Fix | `RESCUE_ISO_DPKG_START_STOP_DAEMON_FAILURE.md` |
| GRUB ohne Theme auf ESP | 🟡 Fix im Workspace, HW pending | `RS_001_GRUB_BRANDING_ANALYSIS.md` |
| Netzwerk-Crash Fallback-TUI | ✅ Fix 1.7.10.2+ | `RS_001_REACT_UI_LAUNCHER_ANALYSIS.md` |
| React/Kiosk fehlt | 🔴 Offen | Kein Browser im SquashFS |
| MSI UEFI-Boot | 🔴 Offen | `RS_001_HW_BOOT_OPERATOR_HANDOFF.md` |
| MSI Netzwerk nach Neustart | 🟡 Teilweise | `RESCUE_MSI_NETWORK_ONBOARDING_FAILURE_TRIAGE.md` |
| RS-001…RS-008 Testmatrix | 🔴 | `docs/testing/RESCUE_STICK_TEST_MATRIX.md` |
| BR-001-OFFLINE Backup-Kette | 🔴 | `release-gates/backup_restore_release_gate.json` |
| Component-Inventory Drift | 🟡 | Runner markiert WLAN/Boot als `missing`, Skripte existieren |

---

## 4. WLAN-Probleme

| Ebene | IST | Gap |
|-------|-----|-----|
| **TUI Live-OS** | `setuphelfer-rescue-network-onboarding`, `setuphelfer_rescue_wifi_scan_and_menu()` in `setuphelfer-rescue-common.sh` | MSI Level-6-Retest ausstehend |
| **Start Assistant** | Netzwerk-Schritt vor Telemetrie | Automatische WLAN-Suche nach Neustart auf MSI historisch nein |
| **React Frontend** | `RescueNetworkPanel.tsx` — nur Platzhalter | Kein Scan, keine API-Verdrahtung |
| **Rescue API** | `wifi_scan_started: false` Default | Backend-Scan nicht an React angebunden |
| **Hauptprodukt** | `ControlCenter.tsx` `scanWifiNetworks()` | Getrennte Codebase, nicht Rescue-Stick |

**Priorität:** TUI stabilisieren und HW nachweisen, bevor React-WLAN implementiert wird.

---

## 5. Telemetrie-Absturz

| Thema | Detail |
|-------|--------|
| Historischer Crash | Inline-Python in Shell → `SyntaxError` (KB-011) |
| Fix | `setuphelfer-rescue-telemetry-build-payload.py` + `setuphelfer-rescue-telemetry-push` |
| Backend | `core/rescue_telemetry_ingest.py`, Router `rescue_telemetry/routers.py` |
| LAN-Proxy | `rescue_telemetry_lan_proxy.py`, DCC `RescueTelemetryLanProxyToolbox.tsx` |
| HW-ACK | MSI-Ingest nicht ausgeführt (`last_ingest_at=null`) |
| Start Assistant | Schritt `_step_telemetry` nach Netzwerk |

**Ampel:** 🟡 Code-Fix da; E2E-Ingest auf Referenzhardware fehlt.

---

## 6. Netzwerkscan

| Kontext | Implementierung | Ampel |
|---------|-----------------|-------|
| Rescue Live TUI | `nmcli rescan` + list, whiptail-Menü | 🟢 |
| Rescue Shell-Menü | `setuphelfer-rescue-network-menu.sh` | 🟢 |
| Rescue React | `RescueNetworkPanel.tsx` — Hinweistext only | 🔴 |
| RescueStartCenter F3 „Netzwerk“ | Kein Handler | 🔴 |

---

## 7. GRUB / Bootmenü

- **ISOLINUX:** 5 Setuphelfer-Einträge + Reboot/Poweroff, `MENU TITLE Setuphelfer Rettungsstick` — 🟢
- **GRUB UEFI:** Rettung, Netzwerk-Assistent, MSI/NVIDIA, Diagnose, toram — 🟡 Theme/Logo ESP
- **Assets:** `assets/rescue/boot-menu/setuphelfer-boot-menu-{de,en}.png`
- **Validation:** `backend/rescue/rescue_graphical_assets.py`, Tests `test_rescue_graphical_assets_v1.py`

---

## 8. Grafischer Startbildschirm

| Asset | Quelle |
|-------|--------|
| Logo | `assets/rescue/logo/setuphelfer-logo2.png` |
| Boot-Menü DE/EN | `assets/rescue/boot-menu/` |
| Splash | `assets/rescue/splash/setuphelfer-splash.png` |
| Icon | `assets/rescue/icons/setuphelfer-icon.png` |
| React UI | `RescueStartCenter.tsx` — visuell, keine Aktionen |

**5/5 required assets** im Workspace — 🟢. Integration auf physischem Stick: 🟡.

---

## 9. Recovery-Menü

### TUI (produktiver Pfad heute)

- `setuphelfer-rescue-start-assistant`: backup, restore, repair, install, diagnostics, expert, quit
- **Alle Write-Aktionen blockiert** — nur Plan-Builder
- State: `wizard-state.json`, `start-assistant-status.json`

### React (Ziel, aktuell Fallback)

- Aktiv: nur `RescueStartCenter`
- Menü: `rescueMenuItems.ts` — enabled: analyze, backup_verify, malware_scan, settings; disabled: backup_create, restore, cloudserver
- **Ungenutzt:** `RescueMainMenu.tsx`, `RescueNetworkPanel.tsx`, `RescueAdvancedOptions.tsx`
- Menü-Klicks: nur `selected` State, keine Navigation

**Capability-Matrix:** `rs001_react_graphical_menu_observed: false`, `rs001_fallback_tui_observed: true`

---

## 10. Priorisierte nächste Schritte (Produkt)

1. **P0:** RS-001 Level-6 HW-Retest (MSI) — Boot, GRUB-Theme, Netzwerk, Telemetrie
2. **P0:** React-Kiosk-Entscheidung (Browser-Stack vs. TUI-first)
3. **P1:** HW-Telemetrie-Ingest nachweisen
4. **P1:** React Rescue UI — WLAN und Menü-Aktionen verdrahten
5. **P2:** Component-Inventory-Runner mit Ist-Stand synchronisieren

---

## Referenzen

- `docs/evidence/rescue/RESCUE_STICK_IST_ANALYSIS.md`
- `docs/evidence/rescue/RESCUE_STICK_GAP_LIST.md`
- `docs/evidence/rescue/RESCUE_STICK_CAPABILITY_MATRIX.yaml`
- `docs/host-env/WISSENSDATENBANK.md` (KB-011…014)
- `docs/testing/RESCUE_STICK_TEST_MATRIX.md`
