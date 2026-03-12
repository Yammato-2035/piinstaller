# Workflow Quickstart: Laptop ↔ Pi

## 🚀 Schnellstart in 5 Minuten

### 1. SSH-Verbindung einrichten

**Auf dem Pi (optional - nur wenn SSH nicht aktiv):**
```bash
# Prüfe SSH-Status
sudo systemctl status ssh

# Falls nicht aktiv:
# sudo systemctl enable ssh && sudo systemctl start ssh

# IP-Adresse notieren
hostname -I
```

**Auf dem Laptop:**

**Prüfe zuerst, ob bereits ein SSH-Key existiert:**
```bash
ls -la ~/.ssh/id_*.pub
```

**Wenn Key vorhanden ist:**
```bash
# Verwende vorhandenen Key (passe den Pfad an)
ssh-copy-id -i ~/.ssh/id_ed25519.pub pi@pi5-gg.local
# oder: ssh-copy-id -i ~/.ssh/id_rsa.pub pi@pi5-gg.local
```

**Wenn kein Key vorhanden ist:**
```bash
# Neuen Key generieren
ssh-keygen -t ed25519 -C "laptop-pi"
ssh-copy-id pi@pi5-gg.local
```

**Testen:**
```bash
ssh pi@pi5-gg.local
```

**SSH-Config optimieren (`~/.ssh/config`):**
```
Host pi
    HostName pi5-gg.local
    User pi
    ServerAliveInterval 60
```

### 2. Repository auf beiden Systemen klonen

**Auf dem Laptop:**
```bash
cd ~/Documents
git clone git@github.com:Yammato-2035/piinstaller.git PI-Installer-Laptop
cd PI-Installer-Laptop
```

**Auf dem Pi:**
```bash
cd ~/Documents
git clone git@github.com:Yammato-2035/piinstaller.git PI-Installer
cd PI-Installer
```

### 3. Scripts nutzen

**Auf dem Laptop (Code entwickeln):**
```bash
cd ~/Documents/PI-Installer-Laptop
# Code entwickeln mit Cursor AI...
./scripts/sync-to-pi.sh "feat: Neue Funktion hinzugefügt"
```

**Auf dem Pi (Dokumentation):**
```bash
cd ~/Documents/PI-Installer
./scripts/update-docs.sh PLAN.md "Planungs-Updates"
```

**Auf dem Pi (Code-Updates holen):**
```bash
cd ~/Documents/PI-Installer
./scripts/sync-from-laptop.sh
```

---

## 📋 Täglicher Workflow

### Morgens
```bash
# Laptop: Neueste Dokumentation holen
cd ~/Documents/PI-Installer-Laptop && git pull

# Pi: Neueste Code-Änderungen holen
cd ~/Documents/PI-Installer && git pull
```

### Während der Arbeit

**Laptop (Code):**
```bash
# Entwickeln...
git add .
git commit -m "feat: Feature X"
git push origin main
```

**Pi (Dokumentation):**
```bash
# Dokumentation bearbeiten...
./scripts/update-docs.sh README.md "Dokumentation aktualisiert"
```

### Abends
```bash
# Beide: Finale Synchronisation
git pull && git push
```

---

## 🎯 Wer macht was?

| Aufgabe | System |
|---------|--------|
| Code schreiben | ✅ **Laptop** (Cursor AI) |
| Dokumentation | ✅ **Pi** |
| Planung | ✅ **Pi** |
| Git Commits | ✅ **Beide** |
| Build/Test | ✅ **Laptop** (lokal) |
| Deployment | ✅ **Pi** (Produktion) |

---

## 🔧 Nützliche Befehle

### Git-Aliases einrichten

**Auf dem Laptop:**
```bash
git config --global alias.sync '!git pull origin main && git push origin main'
git config --global alias.status-short 'status -sb'
```

**Auf dem Pi:**
```bash
git config --global alias.doc '!git add *.md && git commit -m "docs: Update" && git push'
git config --global alias.pull-code 'pull origin main'
```

### Schnelle Synchronisation

```bash
# Laptop: Code pushen
git push origin main

# Pi: Code holen
git pull origin main

# Pi: Dokumentation pushen
git push origin main

# Laptop: Dokumentation holen
git pull origin main
```

---

## ⚠️ Wichtige Regeln

1. ✅ **Code-Dateien** nur auf dem Laptop bearbeiten
2. ✅ **Dokumentationsdateien** primär auf dem Pi bearbeiten
3. ✅ Immer `git pull` vor größeren Änderungen
4. ✅ Klare Commit-Messages verwenden
5. ✅ Regelmäßig synchronisieren (täglich)

---

## 🆘 Bei Problemen

### Merge-Konflikte
```bash
git status                    # Konflikte finden
nano KONFLIKT-DATEI.md        # Manuell lösen
git add KONFLIKT-DATEI.md
git commit -m "fix: Konflikt gelöst"
```

### SSH-Verbindung
```bash
ssh -v pi                     # Verbindung testen
ssh-copy-id pi@pi5-gg.local  # Key neu kopieren
```

### Git-Probleme
```bash
git pull --rebase              # Rebase statt Merge
git push --force-with-lease    # Vorsichtiges Force-Push
```

---

**Vollständige Dokumentation:** Siehe `WORKFLOW_LAPTOP_PI.md`
