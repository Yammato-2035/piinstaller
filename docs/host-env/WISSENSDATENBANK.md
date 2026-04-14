# Wissensdatenbank: Host — Docker Desktop, KVM, MCP

Struktur: **Symptom / Kontext** → **Ursache** → **Nachweis** → **Maßnahme** → **Referenz**.

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
