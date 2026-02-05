# Remote-Entwicklung: Laptop → Raspberry Pi

Du entwickelst auf dem **Laptop** (Cursor/VS Code), der **Code liegt und läuft auf dem Pi**.  
Editor und AI laufen auf dem stärkeren Rechner, Terminal/Build/Run auf dem Pi.

---

## Übersicht

| Komponente | Wo es läuft |
|------------|-------------|
| Cursor / VS Code (UI, AI, Extensions) | **Laptop** |
| Dateien, Terminal, Run/Debug | **Raspberry Pi** (per SSH) |

**Hinweis:** Cursor Remote SSH zum Pi kann mit **404** fehlschlagen, weil Cursor oft keine ARM-Server-Binaries für den Pi bereitstellt. In dem Fall: **VS Code** + Remote SSH nutzen (funktioniert zuverlässig) oder **SSHFS** (siehe Abschnitt „Alternativen“).

---

## 1. Auf dem Raspberry Pi: SSH vorbereiten

### 1.1 SSH aktivieren

Falls noch nicht aktiv:

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh
```

Unter Raspberry Pi OS oft schon an. Prüfen mit: `sudo systemctl status ssh`.

### 1.2 Benutzer & Hostname

- **Benutzername** auf dem Pi (z.B. `pi` oder dein User)
- **Hostname** oder **IP** des Pi im lokalen Netz:
  - Hostname: `pi5-gg.local` (mDNS, Pi heißt Pi5-GG) oder z.B. `mypi`
  - IP: `192.168.1.xy` (mit `hostname -I` auf dem Pi prüfen)

### 1.3 SSH-Key (empfohlen)

Auf dem **Laptop** Schlüssel erzeugen (falls noch keiner existiert):

```bash
ssh-keygen -t ed25519 -C "laptop-pi-dev"
```

Öffentlichen Schlüssel auf den Pi kopieren:

```bash
ssh-copy-id BENUTZER@HOSTNAME_ODER_IP
```

Beispiel: `ssh-copy-id pi@pi5-gg.local` oder `ssh-copy-id pi@192.168.1.50`.

Danach Login ohne Passwort: `ssh pi@pi5-gg.local`.

---

## 2. Auf dem Laptop: Cursor + Remote SSH

### 2.1 Cursor-eigene Remote-SSH-Extension

**Nicht** die Standard-VS-Code-Extension (`ms-vscode-remote.remote-ssh`) nutzen, sondern Cursors eigene:

- **Extension:** `Remote - SSH` von **Anysphere**  
- **ID:** `anysphere.remote-ssh`

In Cursor: **Extensions** (Ctrl+Shift+X) → Suche `@id:anysphere.remote-ssh` → Installieren.

(Diese Version ist für Cursor optimiert und oft stabiler.)

### 2.2 SSH-Config auf dem Laptop

Datei `~/.ssh/config` bearbeiten (oder anlegen):

```bash
nano ~/.ssh/config
```

Eintrag für den Pi (Hostname/IP und User anpassen):

```
Host pi
    HostName pi5-gg.local
    User pi
    # Optional: längeren Timeout für langsame Verbindungen
    ConnectTimeout 120
    ServerAliveInterval 60
    ServerAliveCountMax 6
```

**Bei Verbindungsabbrüchen:** Multiplexing für diesen Host deaktivieren, z.B.:

```
Host pi
    HostName pi5-gg.local
    User pi
    ConnectTimeout 120
    ServerAliveInterval 60
    ServerAliveCountMax 6
    # Multiplexing aus – kann Cursor-Remote stabiler machen
    # ControlPath none
    # ControlMaster no
    # ControlPersist no
```

`ControlPath` etc. nur einkommentieren/anpassen, wenn du sie vorher genutzt hast.

### 2.3 Verbindung herstellen

1. Cursor auf dem **Laptop** öffnen.
2. **Ctrl+Shift+P** → „Remote-SSH: Connect to Host…“.
3. Host wählen (z.B. `pi`) oder `BENUTZER@HOST` eingeben.
4. Neues Fenster öffnet sich, verbunden mit dem Pi.
5. **File → Open Folder** → z.B. `/home/pi/Documents/PI-Installer` (oder dein Projektpfad auf dem Pi).

Ab dann: Editor UI auf dem Laptop, Dateien und integriertes Terminal auf dem Pi.

### 2.4 Timeout erhöhen (falls nötig)

Wenn der Cursor-Server beim ersten Connect lange braucht (v.a. auf Pi):

- In Cursor: **File → Preferences → Settings** → Suche `remote.SSH.connectTimeout`.
- z.B. auf **120** oder **180** (Sekunden) setzen.

---

## 3. Wenn Cursor mit „404“ abbricht (ARM/Pi)

Beim Verbinden versucht Cursor, den **cursor-server** auf dem Pi zu installieren.  
Für ARM (Raspberry Pi) liefert Cursor oft **keine** passenden Builds → Download **404**.

**Symptom:** Fehlermeldung wie „Failed to download VS Code Server“ / „404“ beim Connect.

### Option A: VS Code statt Cursor für Remote zum Pi

1. **VS Code** auf dem Laptop installieren.
2. Extension **Remote - SSH** (`ms-vscode-remote.remote-ssh`) installieren.
3. Dieselbe `~/.ssh/config` nutzen, mit **VS Code** zu `pi` verbinden.
4. Ordner auf dem Pi öffnen wie oben.

VS Code bietet ARM-Server für den Pi, daher funktioniert Remote SSH dort in der Regel.

### Option B: SSHFS + Cursor auf dem Laptop

Pi-Dateisystem per SSH mounten, in Cursor den gemounteten Ordner öffnen:

```bash
# z.B. mit sshfs (Installation: sshfs)
mkdir -p ~/pi-mount
sshfs pi@pi5-gg.local:/home/pi/Documents/PI-Installer ~/pi-mount
```

In Cursor: **File → Open Folder** → `~/pi-mount`.  
Zum Trennen: `fusermount -u ~/pi-mount`.

**Hinweis:** Terminal in Cursor läuft dann lokal. Für Build/Run auf dem Pi zusätzlich z.B. `ssh pi@pi5-gg.local` in einem Terminal nutzen.

---

## 4. Kurz-Checkliste

- [ ] SSH auf dem Pi aktiv, Login (Passwort oder Key) funktioniert.
- [ ] Auf dem Laptop: `ssh pi@pi5-gg.local` (o.ä.) klappt.
- [ ] Cursor: Extension `anysphere.remote-ssh` installiert.
- [ ] `~/.ssh/config` mit Host `pi` (oder deinem Namen) angelegt.
- [ ] Remote-SSH: Connect to Host → Pi auswählen → Ordner auf dem Pi öffnen.
- [ ] Bei 404: VS Code + Remote SSH verwenden oder SSHFS + Cursor.

---

## 5. Nützliche Befehle

| Aktion | Befehl / Ort |
|--------|----------------|
| Pi-IP im Netz | Auf dem Pi: `hostname -I` |
| SSH-Status auf Pi | `sudo systemctl status ssh` |
| Cursor Remote-Logs | Im Remote-Fenster: Output „Remote - SSH“ öffnen |
| Fenster neu laden | Ctrl+Shift+P → „Developer: Reload Window“ |

Bei Fehlern zuerst die **Remote-SSH-Ausgabe** in Cursor prüfen – dort steht meist die konkrete Fehlermeldung (inkl. 404).
