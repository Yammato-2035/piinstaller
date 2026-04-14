# Chat-Zusammenfassung: Docker Desktop, MCP, KVM-Fehler

**Datum:** 2026-04-11  
**Thema:** Installation und Betrieb von Docker Desktop und MCP auf dem Linux-Host (außerhalb des Anwendungscodes); Analyse eines QEMU/KVM-Absturzes.

Diese Datei fasst die **tragfähigen Erkenntnisse** zusammen, damit sie ohne Chat-Verlauf wiederverwendbar sind. Autoritative Detaildokumente: [DOCKER_DESKTOP_AND_MCP.md](DOCKER_DESKTOP_AND_MCP.md), [FAQ.md](FAQ.md), [WISSENSDATENBANK.md](WISSENSDATENBANK.md).

---

## 1. Ausgangslage (Host)

- **OS:** Linux Mint 22.3 (Ubuntu-Basis Noble), Kernel 6.8, x86_64.
- Bereits vorhanden: **Docker Engine** (Ubuntu-Paket, z. B. 29.x), Nutzer in Gruppe `docker`.
- **KVM:** Module geladen (`kvm_amd`), `/dev/kvm` vorhanden; für Nutzer `volker` war per **ACL** Lese-/Schreibzugriff auf `/dev/kvm` gesetzt (nicht zwingend Gruppe `kvm`).
- **QEMU:** `qemu-system-x86_64` 8.2.2 installiert.
- **sysctl:** `kernel.apparmor_restrict_unprivileged_userns = 0` (Voraussetzung für Docker Desktop oft erfüllt).

## 2. Docker Desktop

- **Installation:** Offizielles DEB von `https://desktop.docker.com/linux/main/amd64/docker-desktop-amd64.deb`; Installation mit `sudo apt-get install -y ./docker-desktop-amd64.deb` (interaktives sudo nötig).
- **Start:** `systemctl --user start docker-desktop` oder GUI; Autostart: `systemctl --user enable docker-desktop`.
- **Abgrenzung:** `sudo systemctl start docker` = Host-**Engine**, nicht Docker Desktop.

## 3. MCP (Model Context Protocol)

- Kein monolithischer „ein MCP-Server“ — viele npm-Pakete `@modelcontextprotocol/*`.
- **Praktische Installation ohne sudo:**  
  `npm install -g --prefix ~/.local @modelcontextprotocol/inspector @modelcontextprotocol/server-everything`  
  → Binaries unter `~/.local/bin` (`mcp-inspector`, `mcp-server-everything`).
- **Node:** System oft 18.x; **Inspector** meldet Anforderung **Node ≥ 22.7.5** — für zuverlässigen Betrieb Node 22 LTS empfohlen.
- **Cursor:** MCP-Einträge mit `command`/`args` konfigurieren (Pfad zu Binary oder `npx -y …`).

## 4. Fehleranalyse: „qemu: process terminated unexpectedly: exit status 1“

- **UI-Meldung** ist unspezifisch.
- **Logs:** `~/.docker/desktop/log/host/monitor.log` enthält die Diagnose:
  - `ioctl(KVM_CREATE_VM) failed: 16 Device or resource busy`
  - `failed to initialize kvm: Device or resource busy`
- **Interpretation:** KVM kann zum Zeitpunkt des Starts **nicht** für die Docker-Desktop-VM genutzt werden — häufig durch **parallele Nutzung der Hardware-Virtualisierung**.
- **Beobachtung auf demselben Host:** Laufender Prozess **`VirtualBoxVM`** (Test-VM). Das passt zu **KB-001** in [WISSENSDATENBANK.md](WISSENSDATENBANK.md): VBox-VM beenden, dann Docker Desktop erneut starten.
- **Strategie:** Für Workflows mit **tools/vm-test (VirtualBox)** und Docker Desktop nicht beide gleichzeitig mit laufender VM erwarten; alternativ Host-Docker-Engine nutzen.

## 5. Offene Punkte / Nicht im Chat gelöst

- Langfristige Koexistenz VirtualBox + Docker Desktop ohne manuelles Umschalten (nur Workaround-Ebene dokumentiert).
- Keine automatische Installation ohne Benutzer-sudo.

## 6. Dateiverweise im Repo

| Zweck | Pfad |
|-------|------|
| Index | `docs/host-env/README.md` |
| Hauptdoku | `docs/host-env/DOCKER_DESKTOP_AND_MCP.md` |
| FAQ | `docs/host-env/FAQ.md` |
| Wissensdatenbank | `docs/host-env/WISSENSDATENBANK.md` |
| VM-Test (VBox) | `tools/vm-test/README.md` |

---

*Ende der Zusammenfassung.*
