# SSH und Login (Test-VMs setuphelfer-a / setuphelfer-b)

Dieses Kapitel ist **unabhängig** von Backup und Restore. Ziel: reproduzierbarer **SSH-Zugang per Public Key** und ein **funktionierender Login** (Konsole / optional GUI), ohne die VM-Testskripte mit Geheimnissen zu füttern.

## Ausgangslage im Repo

- Beim Debian-Install legt **du** den Benutzer fest (`INSTALL_GUIDE.md` schlägt `testuser` vor; in den Reports heißt er oft **`user`**).
- **Kein** automatisches Kopieren von Host-Keys in die VM ist Teil von `02-vbox-define-vm.sh` — Keys müssen **einmalig** auf dem Gast landen (oder über dieses Skript).

## Einmal-Fix auf dem Gast (empfohlen, wenn SSH/GUI streikt)

1. In der **VBox-Konsole**: **Strg+Alt+F3** → Text-Login (`tty`).
2. Als **root** einloggen (Root-Passwort aus dem Installer) oder mit einem noch funktionierenden Account **`sudo -i`**.
3. Public Key vom Host bereitstellen, z. B. per **gemeinsamen Ordner** (VBox Shared Folder), USB-Stick oder `nano`:

   ```bash
   # Beispiel: Key-Datei liegt auf /tmp/host.pub (eine Zeile)
   sudo bash /pfad/zum/in-guest-ensure-ssh-and-login.sh /tmp/host.pub volker
   ```

   Oder von der Host-Datei per Umleitung (wenn du den Inhalt in die Zwischenablage kopierst):

   ```bash
   # Auf dem Gast, Zeile einfügen und ausführen:
   cat <<'EOF' | sudo bash /pfad/zum/in-guest-ensure-ssh-and-login.sh - volker
   ssh-ed25519 AAAA… kommentar@host
   EOF
   ```

Das Skript **`scripts/in-guest-ensure-ssh-and-login.sh`**:

- installiert **`openssh-server`** und **`sudo`** (Debian/apt),
- legt **`/etc/ssh/sshd_config.d/70-setuphelfer-vmtest.conf`** an (Pubkey + Passwort aktiv),
- schreibt den Key nach **`~/.ssh/authorized_keys`**, Rechte **700/600**,
- entsperrt das Konto (`passwd -u`) und setzt bei **nologin/false** die Shell auf **`/bin/bash`**,
- startet **`sshd`** neu (nach **`sshd -t`**).

**Härtung danach (Test-VM):** Wenn Key-Login vom Host klappt, in derselben Drop-in-Datei **`PasswordAuthentication no`** setzen und `sudo systemctl reload ssh`.

## Fix vom Host (wenn SSH schon mit Passwort oder altem Key geht)

Voraussetzung: `ssh volker@127.0.0.1 -p 2222` bzw. `-p 2223` antwortet (Passwort oder Key).

```bash
cd tools/vm-test
chmod +x scripts/host-ssh-fix-vm-test-vms.sh scripts/in-guest-ensure-ssh-and-login.sh
# Standard: 127.0.0.1:2222:user und 127.0.0.1:2223:user, Key ~/.ssh/id_ed25519
./scripts/host-ssh-fix-vm-test-vms.sh
```

Anpassen:

```bash
export SSH_KEY="$HOME/.ssh/id_meinkey"
export VM_SSH_TARGETS="127.0.0.1:2222:user 127.0.0.1:2223:testuser"
./scripts/host-ssh-fix-vm-test-vms.sh
```

Das Host-Skript kopiert `in-guest-ensure-ssh-and-login.sh` und die **`.pub`**-Datei nach `/tmp/` auf dem Gast und führt das Gast-Skript mit **`sudo`** aus (ggf. einmal Passwort eingeben).

## Wenn der SSH-Port offen ist, aber kein Banner kommt

Typisch: **sshd** hängt oder die VM ist stark ausgelastet. Nach dem Gast-Skript (oder von tty):

```bash
sudo systemctl restart ssh
sudo journalctl -u ssh -b --no-pager | tail -50
df -h /
```

## GUI-Login weiterhin defekt

Das Gast-Skript richtet **sshd** und Shell/Konto ein, **keinen** Display-Manager. Dann z. B. prüfen: Festplatte voll, falsche Session, Wayland — außerhalb dieses Repo-Minimalpfads.

## VirtualBox: Gast nimmt keine Tastatur an

Wenn **keine Tastatur** im VM-Fenster ankommt, liegt das fast immer an **Fokus / Einfangen** oder an der **Host-Taste**, nicht am Linux-Login selbst.

1. **Einmal ins VM-Fenster klicken** (Fokus). Auf dem Host darf kein anderes Programm die Tastatur abfangen (Bildschirmtastatur, Fernwartung im Vollbild, manche IME-Fenster).
2. **Host-Taste** (VBox-Standard: **rechte Strg**): einmal drücken — oft wechselt die VM zwischen „Tastatur gehört dem Gast“ und „Tastatur gehört dem Host“. Wenn alles beim Host hängen bleibt: **rechte Strg** drücken und erneut ins Fenster klicken.
3. **VBox-Menü** der laufenden VM: **Eingebegeräte → Tastatur → Tastatur einfangen** (oder wieder **freigeben**), falls der Shortcut nicht greift.
4. **Nicht** im **Scale-Modus** testen, wenn es Probleme macht: normales Fenster oder Vollbild (**Host+F**).
5. **Gast-Erweiterungen**: Wenn installiert, manchmal **Maus-Integration** temporär in den VM-Einstellungen prüfen; bei reinem Tastaturproblem zuerst Host-Taste + Fokus.
6. **Alternative ohne Tastatur im Gastfenster:** Vom Host **SSH** nutzen (`ssh -p 2222 user@127.0.0.1`), sobald Netz/NAT und `sshd` laufen — dann brauchst du die Konsole im Fenster nicht zum Tippen.
7. **VBoxManage headless** + nur SSH: VM mit `VBoxManage startvm "NAME" --type headless` starten und ausschließlich über SSH arbeiten (kein grafisches Gastfenster).

Wenn **gar nichts** davon hilft: VM **ausschalten** (nicht nur Save), VirtualBox-**GUI neu starten**, ggf. Host neu anmelden — danach VM erneut starten und Schritt 1–2 wiederholen.

## Kurz-Checkliste

| Schritt | Erledigt |
|--------|----------|
| Pubkey in `~user/.ssh/authorized_keys`, Rechte 600/700 | Skript |
| `openssh-server` aktiv, `sshd -t` ok | Skript |
| Key-Login vom Host: `ssh -p 2222 -i ~/.ssh/id_ed25519 volker@127.0.0.1 true` | manuell |
| Optional: Passwort-Login abschalten | manuell |
