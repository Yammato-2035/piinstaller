# Docker Desktop und MCP auf dem Linux-Host

Stand: April 2026. Zielgruppe: Maintainer, die Container lokal mit Docker Desktop nutzen und MCP-Server für Cursor o. Ä. einbinden.

## 1. Docker Desktop installieren (DEB)

Offizielle Quelle: [Install Docker Desktop on Ubuntu](https://docs.docker.com/desktop/setup/install/linux/ubuntu/).

1. Paket herunterladen (AMD64):  
   `https://desktop.docker.com/linux/main/amd64/docker-desktop-amd64.deb`
2. Installieren:
   ```bash
   sudo apt-get update
   sudo apt-get install -y ./docker-desktop-amd64.deb
   ```
3. Hinweis von Docker: Am Ende kann `apt` eine harmlose Meldung zu „unsandboxed … Permission denied“ zeigen — oft ignorierbar.

**Parallelbetrieb:** Auf demselben Host kann bereits **Docker Engine** (Paket `docker.io` / `docker-ce`) laufen. Docker Desktop nutzt einen **eigenen Kontext** und eine eigene VM; es kann zu Überschneidungen mit dem klassischen Docker-Socket kommen — Kontext in Docker Desktop prüfen bzw. einen der Dienste beenden, wenn etwas hängt.

**Voraussetzungen (Kurz):**

- x86-64, unterstützte Ubuntu-Version (Linux Mint mit passender Ubuntu-Basis ist üblich).
- Virtualisierung im BIOS/UEFI aktiv (`vmx`/`svm` in `/proc/cpuinfo`).
- Für `/dev/kvm`: Gerät vorhanden; Nutzer in Gruppe `kvm` oder passende ACLs (siehe FAQ).
- Optional laut Doku: `gnome-terminal`, wenn kein GNOME.
- `kernel.apparmor_restrict_unprivileged_userns=0` kann für Docker Desktop nötig sein (siehe Docker-Doku).

## 2. Docker Desktop starten und beenden

- **GUI:** Anwendungsmenü → Docker Desktop (Lizenzdialog beim ersten Start).
- **Terminal:**
  ```bash
  systemctl --user start docker-desktop
  systemctl --user stop docker-desktop
  ```
- **Autostart:**
  ```bash
  systemctl --user enable docker-desktop
  ```
  Oder in Docker Desktop: *Settings → General → Start Docker Desktop when you sign in*.

**Nicht verwechseln:** `sudo systemctl start docker` startet die **Host-Docker-Engine**, nicht Docker Desktop.

## 3. Fehler: „qemu: process terminated unexpectedly: exit status 1“

Die UI-Meldung ist nur die Folge. In den Logs steht typischerweise:

```text
ioctl(KVM_CREATE_VM) failed: 16 Device or resource busy
failed to initialize kvm: Device or resource busy
```

**Häufigste Ursache auf Entwicklerrechnern:** Parallel laufende **VirtualBox-VMs** (oder andere KVM-Nutzer). Virtualisierung ist dann für QEMU/KVM von Docker Desktop nicht sauber nutzbar.

**Vorgehen:**

1. Alle VirtualBox-VMs beenden; Prozess `VirtualBoxVM` sollte nicht mehr laufen.
2. Docker Desktop neu starten.
3. Siehe ausführlich: [WISSENSDATENBANK.md](WISSENSDATENBANK.md) und [FAQ.md](FAQ.md).

**Log-Pfad:** `~/.docker/desktop/log/host/monitor.log` (und weitere Dateien im gleichen Verzeichnis).

## 4. MCP-Server (Model Context Protocol)

Es gibt kein einzelnes Paket „der MCP-Server“; Server sind pro Tool konfigurierbar (z. B. Cursor unter *MCP*).

**Variante ohne Root — Installation unter `~/.local`:**

```bash
mkdir -p ~/.local/bin
npm install -g --prefix ~/.local @modelcontextprotocol/inspector @modelcontextprotocol/server-everything
```

- `~/.local/bin/mcp-inspector` — Debugging/Inspektion von MCP-Servern.
- `~/.local/bin/mcp-server-everything` — Referenzserver mit vielen Demo-Tools.

**Node-Version:** Viele aktuelle MCP-Pakete erwarten **Node 20+** bzw. der Inspector **≥ 22.7.5**. Bei älterem System-Node (z. B. 18.x) Node 22 LTS nachinstallieren (z. B. nvm oder NodeSource), damit Warnungen und Laufzeitfehler vermieden werden.

**Cursor:** In den MCP-Einstellungen `command` + `args` setzen, z. B. `mcp-server-everything` oder vollständiger Pfad `~/.local/bin/mcp-server-everything`.

**Alternative:** Server per `npx -y @modelcontextprotocol/...` starten (ohne globale Installation).

## 5. Diagnose sammeln (Docker Desktop)

Über die Docker-Desktop-Oberfläche: Troubleshooting → Diagnose erstellen; oder die genannten Logdateien unter `~/.docker/desktop/log/` anhängen.

## 6. Weiterführende Links

- [Docker Desktop Linux – Ubuntu](https://docs.docker.com/desktop/setup/install/linux/ubuntu/)
- [Docker Desktop Troubleshooting](https://docs.docker.com/desktop/troubleshoot/overview/)
- [Model Context Protocol](https://modelcontextprotocol.io/) (Spezifikation und Ökosystem)
