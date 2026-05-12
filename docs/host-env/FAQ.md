# FAQ: Docker Desktop, MCP und KVM (Linux-Host)

## Wie starte ich Docker Desktop?

Über das Anwendungsmenü oder:

```bash
systemctl --user start docker-desktop
```

Autostart: `systemctl --user enable docker-desktop` oder in den Docker-Desktop-Einstellungen aktivieren.

## Was ist der Unterschied zu `systemctl start docker`?

`docker` (systemd, oft mit `sudo`) ist die **Docker Engine direkt auf dem Host**. Docker Desktop ist eine **eigene Anwendung** mit VM und eigenem Kontext — das startet **nicht** über den klassischen `docker.service` des Hosts.

## Docker Desktop meldet „qemu: process terminated unexpectedly: exit status 1“ — was tun?

1. In `~/.docker/desktop/log/host/monitor.log` nach `KVM_CREATE_VM` bzw. `Device or resource busy` suchen.
2. **VirtualBox-VMs beenden** (und VirtualBox-Prozesse schließen), andere QEMU/KVM-Nutzer prüfen.
3. Docker Desktop erneut starten.

Details: [WISSENSDATENBANK.md](WISSENSDATENBANK.md), Eintrag *KVM busy*.

## Brauche ich die Gruppe `kvm`?

Wenn `/dev/kvm` nur für `root:kvm` lesbar/schreibbar ist, sollte der Nutzer in `kvm` sein:

```bash
sudo usermod -aG kvm "$USER"
```

Danach **neu anmelden**. Wenn für deinen Nutzer eine ACL auf `/dev/kvm` gesetzt ist, kann es auch ohne Gruppenmitgliedschaft funktionieren — mit `getfacl /dev/kvm` prüfen.

## Kann ich Docker Desktop und VirtualBox gleichzeitig nutzen?

Oft **nicht zuverlässig** für gleichzeitige **laufende VMs**: Beide wollen Hardware-Virtualisierung; KVM von Docker Desktop kann mit **EBUSY** abbrechen, solange VirtualBox-VMs laufen. Für längere Sessions: entweder VBox-VMs stoppen oder statt Docker Desktop die **Host-Docker-Engine** nutzen.

## Wie installiere ich „den“ MCP-Server?

Es gibt viele Server-Pakete (`@modelcontextprotocol/server-*`). Üblich: per **npm global** (ggf. mit `--prefix ~/.local`) oder **`npx -y …`**. In **Cursor** unter MCP den `command`/`args` eintragen. Siehe [DOCKER_DESKTOP_AND_MCP.md](DOCKER_DESKTOP_AND_MCP.md).

## Warum warnt npm beim Inspector wegen der Node-Version?

Neuere `@modelcontextprotocol/inspector`-Versionen deklarieren **Node ≥ 22.7.5**. Unter älterem Node kann es trotz Installation laufen oder früh scheitern — **Node 22 LTS** installieren, wenn du den Inspector produktiv nutzt.

## Wo liegt das Docker-Desktop-DEB?

Aktuell wird es von Docker bereitgestellt unter  
`https://desktop.docker.com/linux/main/amd64/docker-desktop-amd64.deb`  
(Version siehe [Release Notes](https://docs.docker.com/desktop/release-notes/)).
