# SSH Setup Troubleshooting

## Problem: Connection refused auf Port 22

Wenn du den Fehler `Connection refused` bekommst, bedeutet das, dass SSH auf dem Pi nicht erreichbar ist.

### Lösungsschritte:

#### 1. Auf dem Raspberry Pi prüfen (direkt am Pi oder per physischem Zugriff):

**SSH-Dienst aktivieren:**
```bash
# Status prüfen
sudo systemctl status ssh

# SSH aktivieren und starten
sudo systemctl enable ssh
sudo systemctl start ssh

# Status erneut prüfen
sudo systemctl status ssh
```

**Port prüfen:**
```bash
# Prüfe ob SSH auf Port 22 hört
sudo netstat -tlnp | grep :22
# oder
sudo ss -tlnp | grep :22
```

**Firewall prüfen (falls UFW installiert):**
```bash
# Firewall-Status
sudo ufw status

# Port 22 freigeben (falls Firewall aktiv)
sudo ufw allow 22/tcp
sudo ufw reload
```

**Oder nutze das Diagnose-Script:**
```bash
cd ~/Documents/PI-Installer
./scripts/check-ssh-on-pi.sh
```

#### 2. Alternative: SSH über anderen Port

Falls SSH auf einem anderen Port läuft:

**Auf dem Pi prüfen:**
```bash
sudo grep "^Port" /etc/ssh/sshd_config
```

**SSH-Config auf dem Laptop anpassen:**
```bash
nano ~/.ssh/config
```

Füge Port hinzu:
```
Host pi
    HostName 192.168.178.68
    User pi
    Port 2222    # Oder welcher Port auch immer
    IdentityFile ~/.ssh/id_ed25519_pi
```

#### 3. Manuelle Verbindung testen

**Vom Laptop aus:**
```bash
# Verbindung testen (mit Passwort)
ssh pi@192.168.178.68

# Falls Port anders:
ssh -p 2222 pi@192.168.178.68
```

### Schnelllösung (wenn du physischen Zugriff auf den Pi hast):

```bash
# Auf dem Pi ausführen:
sudo systemctl enable ssh
sudo systemctl start ssh
sudo ufw allow 22/tcp 2>/dev/null || echo "UFW nicht installiert"
```

Dann vom Laptop testen:
```bash
ssh pi@192.168.178.68
```

### Wenn SSH immer noch nicht funktioniert:

1. **Prüfe ob der Pi erreichbar ist:**
   ```bash
   ping 192.168.178.68
   ```

2. **Prüfe ob ein anderer Service auf Port 22 läuft:**
   ```bash
   sudo netstat -tlnp | grep :22
   ```

3. **Prüfe SSH-Logs auf dem Pi:**
   ```bash
   sudo journalctl -u ssh -n 50
   ```

4. **SSH-Konfiguration prüfen:**
   ```bash
   sudo sshd -T | grep -E "port|listenaddress"
   ```

### Nach erfolgreicher SSH-Aktivierung:

Sobald SSH funktioniert, kopiere den SSH-Key:

```bash
# Vom Laptop aus:
ssh-copy-id -i ~/.ssh/id_ed25519_pi.pub pi@192.168.178.68

# Oder manuell (siehe WORKFLOW_LAPTOP_PI.md)
```

---

**Hinweis:** Wenn du keinen physischen Zugriff auf den Pi hast und SSH nicht aktiviert ist, musst du entweder:
- Den Pi physisch anschließen (Monitor/Tastatur)
- VNC/Remote Desktop nutzen (falls aktiviert)
- Den Pi neu starten und beim ersten Boot SSH aktivieren (bei Raspberry Pi OS möglich)
