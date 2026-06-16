# Wissensdatenbank: Host — Docker Desktop, KVM, MCP, Rettungsstick

Struktur: **Symptom / Kontext** → **Ursache** → **Nachweis** → **Maßnahme** → **Referenz**.

**Rettungsstick (KB-011 … KB-014):** Überblick in [RESCUE_START_ASSISTANT_OVERVIEW.md](../knowledge-base/rescue/RESCUE_START_ASSISTANT_OVERVIEW.md), FAQ in [RESCUE_STICK_FAQ_DE.md](../faq/RESCUE_STICK_FAQ_DE.md).

---

## KB-001: QEMU exit status 1 bei Docker Desktop (Linux)

| Feld | Inhalt |
|------|--------|
| **Symptom** | Dialog: „Docker Desktop encountered an unexpected error…“; Text erwähnt `qemu: process terminated unexpectedly: exit status 1`. |
| **Kontext** | Linux-Host mit KVM-fähiger CPU; Docker Desktop 4.x. |
| **Ursache (häufig)** | `KVM_CREATE_VM` schlägt mit **errno 16 (EBUSY)** fehl — KVM/Hardware-Virtualisierung ist belegt oder kurzzeitig nicht exclusiv nutzbar. Typisch: **laufende VirtualBox-VM** (`VirtualBoxVM`), seltener andere KVM-QEMU-Instanzen, libvirt, bestimmte Emulator-Stacks. |
| **Nachweis** | Datei `~/.docker/desktop/log/host/monitor.log` durchsuchen nach: `ioctl(KVM_CREATE_VM)`, `Device or resource busy`, `failed to initialize kvm`. Optional: laufende Prozesse `pgrep -a VirtualBoxVM` / `pgrep -a qemu-system`. |
| **Maßnahme** | 1) Alle VirtualBox-VMs ordentlich herunterfahren. 2) Docker Desktop neu starten (`systemctl --user restart docker-desktop` oder App). 3) Wenn dauerhaft beides gebraucht wird: für Containerzeiten ohne Desktop-VM die **Host-Docker-Engine** nutzen oder nur eine Virtualisierungstechnik gleichzeitig betreiben. |
| **Verwandt** | `tools/vm-test`-Workflow nutzt VirtualBox — vor Docker-Desktop-Start VBox-VMs beenden. |

---

## KB-002: Docker Desktop installieren, sudo nicht automatisierbar

| Feld | Inhalt |
|------|--------|
| **Symptom** | Automatisierte Installation scheitert an `sudo` (Passwort/TTY). |
| **Ursache** | `apt install ./docker-desktop-amd64.deb` erfordert Root-Rechte. |
| **Maßnahme** | DEB manuell herunterladen; `sudo apt-get install -y ./docker-desktop-amd64.deb` interaktiv ausführen. |
| **Referenz** | [DOCKER_DESKTOP_AND_MCP.md](DOCKER_DESKTOP_AND_MCP.md) §1 |

---

## KB-003: Parallel Docker Engine (Host) und Docker Desktop

| Feld | Inhalt |
|------|--------|
| **Symptom** | Verwirrung, welcher `docker`-Befehl welche Engine anspricht; Socket-Konflikte. |
| **Ursache** | Zwei Installationen: systemd-`docker` vs. Docker-Desktop-VM + Kontext. |
| **Maßnahme** | `docker context ls` / in Docker Desktop den aktiven Kontext prüfen. Bei Problemen einen Dienst beenden bzw. nur eine Variante für eine Session nutzen. |
| **Referenz** | Docker-Dokumentation zu [contexts](https://docs.docker.com/engine/context/working-with-contexts/). |

---

## KB-004: MCP-Pakete unter ~/.local, Node-Version

| Feld | Inhalt |
|------|--------|
| **Symptom** | `npm WARN EBADENGINE` beim Installieren von `@modelcontextprotocol/inspector`. |
| **Ursache** | Paket fordert neueres Node als das System-`nodejs` (z. B. 18.x). |
| **Maßnahme** | Node 22 LTS installieren (nvm, Paketquelle, etc.); oder nur `server-everything`/`npx` mit kompatiblem Node nutzen. |
| **Installationspfad** | `npm install -g --prefix ~/.local <paket>`; Binaries unter `~/.local/bin` (in PATH aufnehmen). |

---

## KB-005: /dev/kvm und Rechte

| Feld | Inhalt |
|------|--------|
| **Symptom** | QEMU kann KVM nicht öffnen (andere Meldung als EBUSY, z. B. Permission denied). |
| **Ursache** | Nutzer nicht in Gruppe `kvm`, keine ACL; oder KVM-Modul nicht geladen. |
| **Maßnahme** | `ls -la /dev/kvm`; `groups`; `lsmod \| grep kvm`; ggf. `sudo usermod -aG kvm "$USER"` und Neu-Anmeldung; `getfacl /dev/kvm` bei ACL-Setups. |

---

## Log- und Konfigurationspfade (Referenz)

| Pfad | Zweck |
|------|--------|
| `~/.docker/desktop/log/host/monitor.log` | QEMU/KVM/Engine-Fehler |
| `~/.docker/desktop/log/host/com.docker.backend.log` | Backend, allgemein |
| `~/.docker/desktop/log/vm/` | Gast-VM-Logs |
| `~/.local/bin/mcp-*` | Benutzerlokal installierte MCP-CLI-Tools |

---

*Einträge können bei neuen Fällen um KB-006 ff. ergänzt werden.*

---

## KB-006: Development Control Center zeigt Session, aber keinen neuen VM-Knoten

| Feld | Inhalt |
|------|--------|
| **Symptom** | In **Lab Sessions** ist ein QEMU-Lauf sichtbar, im Development-Server-Knotenbereich erscheint keine neue VM. |
| **Ursache** | Erwartbares Phase-1-Verhalten: Host-Session wird sofort geschrieben, Guest-Node erst bei erfolgreichem Ingest (`dev_server_report_new=true`). |
| **Nachweis** | Fleet-Session-Status vorhanden (`starting/booting/...`), aber `guest.report_seen=false` bzw. Finding `guest_report_missing`. |
| **Maßnahme** | Nicht als „Fake-VM fehlt“ interpretieren. Zuerst Session- und Serial-Befund auswerten, dann getrennt Ingest-/Agent-Ursache prüfen. |
| **Referenz** | `docs/evidence/dev-dashboard/FLEET_SESSION_PHASE1_RESULT.md` |

---

## KB-007: QEMU Timeout 124 in Fleet Session

| Feld | Inhalt |
|------|--------|
| **Symptom** | Session endet mit `status=timeout`, `qemu_exit_code=124`. |
| **Ursache** | QEMU wurde durch den Wrapper-Timeout beendet (z. B. Gast bootet nicht vollständig oder Autopilot liefert keinen Abschluss). |
| **Nachweis** | Session-Finding `qemu_timeout_124`; in Evidence `qemu_autopilot_result.json` mit `qemu_exit_code: 124`. |
| **Maßnahme** | Kein Blind-Retry. Serial-Log klassifizieren (Bootloader/Kernel/systemd/Marker) und dann gezielt die nächste Analysefrage stellen. |
| **Referenz** | `docs/evidence/rescue/QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` |

---

## KB-008: `serial_empty` trotz laufendem Smoke

| Feld | Inhalt |
|------|--------|
| **Symptom** | Session zeigt `serial_empty`, Serial-Log bleibt 0 Bytes. |
| **Ursache** | Früher häufig bei unzureichender Serial-Ausgabe im Bootpfad; Phase-1 bewertet dies als Warning statt Hard-Fail. |
| **Nachweis** | `serial.size_bytes=0`, Finding `serial_empty`, aber Session kann weiterhin heartbeaten. |
| **Maßnahme** | Als Diagnose-Hinweis behandeln: Bootloader-/Kernel-Serial-Pfad und Wrapper-Capture prüfen; kein automatischer Abbruch als Infrastruktur-Fail. |
| **Referenz** | `docs/architecture/DEV_CONTROL_CENTER_FLEET_SESSION_CONTRACT.md` |

---

## KB-009: Fleet Session Phase 1 Live-Abnahme (ohne QEMU) erfolgreich

| Feld | Inhalt |
|------|--------|
| **Symptom / Kontext** | Live-Runtime-Abnahme gegen `/opt/setuphelfer` sollte Fleet-API und Session-Semantik ohne QEMU belegen. |
| **Nachweis** | `local_lab` aktiv, `/api/fleet/sessions*` live `HTTP 200`, manueller Run `manual_fleet_phase1_acceptance_20260602_125333` mit final `timeout`, `qemu.exit_code=124`, `serial_empty`, `guest_report_missing`; Persistenz unter `/opt/setuphelfer/docs/evidence/runtime-results/dev-dashboard/fleet_sessions*.json*`; danach `release` wiederhergestellt mit Fleet-Routen `HTTP 404 PROFILE_ROUTE_BLOCKED`. |
| **Maßnahme** | Für profilabhängige Runtime-Schritte immer interaktives Operator-`sudo` nutzen; Abnahme strikt in Reihenfolge `release -> local_lab -> smoke -> release` durchführen. |
| **Referenz** | `docs/evidence/dev-dashboard/FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` |

---

## KB-010: Fleet Heartbeat liefert `invalid_status`

| Feld | Inhalt |
|------|--------|
| **Symptom** | `POST /api/fleet/sessions/{session_id}/heartbeat` antwortet mit `FLEET_SESSION_BLOCKED_INVALID_PAYLOAD` und Fehler `invalid_status`. |
| **Ursache** | Heartbeat-Payload nutzt `status=running`, dieser Wert ist nicht Teil der erlaubten Fleet-Statusmenge. |
| **Nachweis** | Live-Abnahme-Lauf zeigt Heartbeat-Blockierung bei ansonsten erfolgreichem create/finish/final read. |
| **Maßnahme** | Heartbeat nur mit erlaubten Statuswerten senden (z. B. `starting`, `booting`, `serial_active`, `timeout_warning`) oder `status` im Heartbeat weglassen. |
| **Referenz** | `backend/core/fleet_session_state.py`, `docs/evidence/dev-dashboard/FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` |

---

## KB-011: Rettungsstick — Telemetrie SyntaxError (behoben ab 1.7.6.0)

| Feld | Inhalt |
|------|--------|
| **Symptom** | Auf MSI: `setuphelfer-rescue-telemetry-push` bricht ab mit `SyntaxError: unterminated string literal` (ca. Zeile 31). |
| **Ursache** | Inline-Python-Heredoc: `json.loads("""` + `json.dumps(lsblk)` → vier Anführungszeichen `""""` → ungültiges Python. |
| **Fix** | Separates Modul `setuphelfer-rescue-telemetry-build-payload.py`; Shell-Wrapper ohne JSON-Injection im Heredoc. |
| **Referenz** | `docs/knowledge-base/rescue/RESCUE_START_ASSISTANT_OVERVIEW.md`, Evidence `RESCUE_TELEMETRY_PUSH_AUTOMATION_AND_BRANDED_BOOT_MENU_FIX_RESULT.md` |

---

## KB-012: Rettungsstick — Boot-Menü fehlt in ISO

| Feld | Inhalt |
|------|--------|
| **Symptom** | ISO bootet, `isolinux/live.cfg` enthält nur Debian-Default; kein MSI-/Diagnose-/toram-Eintrag. |
| **Ursache** | Binary-Hook schrieb ISOLINUX mit falscher Syntax (`LABEL`/`LINUX` statt `label`/`kernel`). |
| **Fix (1.7.7.0)** | Menü-Snippet in `live.cfg.in` beim Prepare + korrigierter Hook; `MENU TITLE Setuphelfer Rettungsstick`. |
| **Nachweis** | `grep setuphelfer-rescue-default config/bootloaders/isolinux/live.cfg.in` nach Prepare. |
| **Referenz** | `scripts/rescue-live/image/setuphelfer-rescue-boot-menu-snippet.cfg` |

---

## KB-013: Rettungsstick — WLAN-Menü bricht ab / kein Passwort

| Feld | Inhalt |
|------|--------|
| **Symptom** | OK/Return im WLAN-Menü beendet Assistent oder verbindet falsches Netz; Passwortabfrage fehlt. |
| **Ursache** | whiptail lieferte Tag-Nummer statt SSID; `set -e` bei Escape; Boot-Trigger ohne interaktiven Pfad. |
| **Fix (1.7.7.0)** | Index→SSID-Mapping, `--passwordbox`, Offline-Exit 20, Start Assistant auf tty1. |
| **Referenz** | `scripts/rescue-live/image/setuphelfer-rescue-common.sh` (`setuphelfer_rescue_wifi_scan_and_menu`) |

---

## KB-014: Rettungsstick — ISO-Validate blockiert (stale chroot)

| Feld | Inhalt |
|------|--------|
| **Symptom** | `validate-controlled-live-build-tree.sh` endet mit `FORBIDDEN: chroot/.../firmware/...` oder root-owned Artefakte. |
| **Ursache** | Vorheriger `lb build` hinterließ root-owned `chroot/`/`binary/` — Validate ist read-only-strikt. |
| **Maßnahme** | `sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean`, dann Prepare + Validate erneut. **Kein** `rm -rf` auf gemounteten Pfaden. |
| **Referenz** | `docs/faq/rescue_iso_build_faq.md` (Chroot-Cleanup), Prompt `RESCUE_START_ASSISTANT_ISO_REBUILD_OPERATOR_COMPLETION` |
