# Workflow-Aufteilung: Laptop ↔ Raspberry Pi

Diese Anleitung beschreibt, wie du den **Laptop** für intensive Entwicklungsaufgaben (Cursor AI, Code-Entwicklung) nutzt und der **Raspberry Pi** Dokumentation, Versionierung und Planungsaufgaben übernimmt.

**Hinweis:** Cursor kann auch **direkt auf dem Pi** laufen (z. B. auf Pi5-GG). Dann entfällt die SSH-Verbindung vom Laptop; alle Befehle und das Repository liegen lokal auf dem Pi.

---

## 🎯 Übersicht: Wer macht was?

| Aufgabe | Laptop | Raspberry Pi |
|---------|--------|--------------|
| **Code-Entwicklung** | ✅ Cursor AI, IntelliSense, Debugging | ❌ |
| **Build & Test** | ✅ Lokale Tests | ✅ Produktionstests |
| **Dokumentation** | 📝 Schreiben/Editieren | ✅ Verwaltung, Versionierung |
| **Git Operations** | ✅ Commits, Branches | ✅ Repository-Verwaltung, Sync |
| **Planung** | 📋 Ideen sammeln | ✅ Strukturierung, Tracking |
| **Deployment** | ❌ | ✅ Produktions-Deployment |

---

## 🔧 Setup: Verbindung zwischen Laptop und Pi

### 1. SSH-Verbindung einrichten

#### Auf dem Raspberry Pi:

**Schritt 1: SSH-Status prüfen (optional, falls bereits aktiv)**

```bash
# Prüfe ob SSH läuft
sudo systemctl status ssh

# Falls SSH nicht aktiv ist, aktiviere es:
# sudo systemctl enable ssh
# sudo systemctl start ssh
```

**Schritt 2: IP-Adresse oder Hostname notieren**

Der Pi ist im Netzwerk **nur per WLAN** verbunden (nicht über Ethernet/eth0). Für die Verbindung nutze die WLAN-IP oder besser den Hostname per mDNS.

```bash
# IP-Adresse herausfinden (zeigt die WLAN-IP)
hostname -I
# Beispiel: 192.168.1.50

# Oder Hostname verwenden (mDNS) – bei WLAN besonders praktisch, da die IP sich ändern kann
hostname
# Beispiel: Pi5-GG → dann: pi5-gg.local
```

**Hinweis:** Wenn SSH bereits aktiv ist (wie bei dir), kannst du diesen Schritt überspringen und direkt mit der IP-Adresse/Hostname fortfahren. Bei reiner WLAN-Nutzung ist `pi5-gg.local` (Hostname Pi5-GG) oft zuverlässiger als eine feste IP.

#### Auf dem Laptop:

**Schritt 1: Prüfen, ob bereits ein SSH-Key existiert**

```bash
# Prüfe auf vorhandene SSH-Keys
ls -la ~/.ssh/id_*.pub

# Oder spezifisch für ed25519 (empfohlen)
ls -la ~/.ssh/id_ed25519.pub

# Oder für RSA (älterer Standard)
ls -la ~/.ssh/id_rsa.pub
```

**Schritt 2a: Wenn bereits ein Key vorhanden ist (empfohlen)**

```bash
# Verwende den vorhandenen Key - kopiere ihn auf den Pi
ssh-copy-id -i ~/.ssh/id_ed25519.pub BENUTZER@PI_IP_ODER_HOSTNAME
# Beispiel: ssh-copy-id -i ~/.ssh/id_ed25519.pub pi@192.168.1.50
# oder: ssh-copy-id -i ~/.ssh/id_ed25519.pub pi@pi5-gg.local

# Falls du RSA verwendest:
# ssh-copy-id -i ~/.ssh/id_rsa.pub pi@pi5-gg.local
```

**Schritt 2b: Wenn kein Key vorhanden ist**

```bash
# SSH-Key generieren (ed25519 ist sicherer und schneller)
ssh-keygen -t ed25519 -C "laptop-pi-workflow"

# Bei der Abfrage nach Speicherort: Enter drücken für Standard (~/.ssh/id_ed25519)
# Bei der Abfrage nach Passphrase: Enter für keine Passphrase ODER Passphrase eingeben für mehr Sicherheit

# Öffentlichen Schlüssel auf den Pi kopieren
ssh-copy-id BENUTZER@PI_IP_ODER_HOSTNAME
# Beispiel: ssh-copy-id pi@192.168.1.50
# oder: ssh-copy-id pi@pi5-gg.local
```

**Schritt 3: Verbindung testen**

```bash
# Teste die Verbindung (ohne Passwort, wenn Key richtig kopiert wurde)
ssh pi@pi5-gg.local
# oder: ssh BENUTZER@PI_IP

# Falls es nicht funktioniert, prüfe den Key-Typ:
cat ~/.ssh/id_ed25519.pub  # oder id_rsa.pub
```

### 2. SSH-Config auf dem Laptop optimieren

Bearbeite `~/.ssh/config` auf dem Laptop:

```bash
nano ~/.ssh/config
```

Füge hinzu (passe `IdentityFile` an deinen vorhandenen Key an):
```
Host pi
    HostName pi5-gg.local
    User pi
    IdentityFile ~/.ssh/id_ed25519    # Oder ~/.ssh/id_rsa wenn du RSA verwendest
    ServerAliveInterval 60
    ServerAliveCountMax 6
    # Für Git-Operationen optimiert
    ControlMaster auto
    ControlPath ~/.ssh/control-%h-%p-%r
    ControlPersist 10m
```

**Wichtig:** Wenn du einen anderen Key-Typ verwendest (z.B. RSA statt ed25519), ändere `IdentityFile` entsprechend:
- RSA: `IdentityFile ~/.ssh/id_rsa`
- ed25519: `IdentityFile ~/.ssh/id_ed25519`
- ECDSA: `IdentityFile ~/.ssh/id_ecdsa`

**Key-Typ herausfinden:**
```bash
# Zeige alle vorhandenen öffentlichen Keys
ls -la ~/.ssh/id_*.pub

# Zeige Inhalt des Keys (erste Zeile zeigt den Typ)
head -1 ~/.ssh/id_ed25519.pub  # z.B. "ssh-ed25519 ..."
```

Jetzt kannst du einfach `ssh pi` verwenden.

---

## 📁 Repository-Struktur: Lokal vs. Remote

### Auf dem Laptop (Hauptentwicklung)

```bash
# Repository auf dem Laptop klonen
cd ~/Documents
git clone git@github.com:DEIN-USERNAME/PI-Installer.git PI-Installer-Laptop
cd PI-Installer-Laptop

# Entwicklungsumgebung einrichten
cd frontend && npm install
cd ../backend && python3.12 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

**Aufgaben auf dem Laptop:**
- ✅ Code schreiben und entwickeln
- ✅ Cursor AI für Code-Generierung nutzen
- ✅ Lokale Tests durchführen
- ✅ Commits erstellen
- ✅ Branches erstellen und mergen

### Auf dem Raspberry Pi (Dokumentation & Verwaltung)

```bash
# Repository auf dem Pi klonen (oder bereits vorhanden)
cd ~/Documents
git clone git@github.com:DEIN-USERNAME/PI-Installer.git PI-Installer
cd PI-Installer

# Git-Config für Dokumentations-Workflow
git config user.name "PI-Dokumentation"
git config user.email "pi@pi5-gg.local"
```

**Desktop-Starter anlegen (Backend, Frontend, App-Fenster, Browser):**

```bash
cd ~/Documents/PI-Installer
bash scripts/desktop-launcher-alle-anlegen.sh
```

Danach liegen auf dem Desktop (bzw. Schreibtisch):
- **PI-Installer Backend starten**
- **PI-Installer Frontend starten** (nur Vite-Server)
- **PI-Installer Frontend (App-Fenster)** (eigene Oberfläche / Tauri)
- **PI-Installer Frontend (Browser)** (öffnet im Standard-Browser)

**Wichtig:** Beim **App-Fenster** (Tauri) und **Browser** muss das **Backend zuerst laufen** („PI-Installer Backend starten“), sonst schlagen Sudo-Passwort-Speicherung und API-Aufrufe fehl („Backend erreichbar?“). Reihenfolge: zuerst Backend starten, dann Frontend.

**Aufgaben auf dem Pi:**
- ✅ Dokumentations-Updates (`*.md` Dateien)
- ✅ Planungsdateien (`PLAN.md`, `*.plan.md`)
- ✅ Versionsverwaltung (`VERSION`)
- ✅ Changelog-Updates
- ✅ Repository-Synchronisation

---

## 🔄 Workflow: Synchronisation zwischen Laptop und Pi

### Szenario 1: Code-Entwicklung auf dem Laptop

```bash
# Auf dem LAPTOP:
cd ~/Documents/PI-Installer-Laptop

# Feature entwickeln, Code schreiben...
# (Cursor AI hilft dabei)

# Änderungen committen
git add .
git commit -m "feat: Neue Feature-Implementierung"

# Auf GitHub pushen
git push origin main
```

### Szenario 2: Dokumentation auf dem Pi aktualisieren

```bash
# Auf dem RASPBERRY PI:
cd ~/Documents/PI-Installer

# Neueste Änderungen vom GitHub holen
git pull origin main

# Dokumentation bearbeiten (z.B. PLAN.md)
nano PLAN.md
# oder mit einem einfachen Editor

# Dokumentations-Änderungen committen
git add PLAN.md
git commit -m "docs: Planungs-Updates"

# Auf GitHub pushen
git push origin main
```

### Szenario 3: Synchronisation beider Repositories

```bash
# Auf dem LAPTOP - Änderungen vom Pi holen:
cd ~/Documents/PI-Installer-Laptop
git pull origin main

# Auf dem PI - Änderungen vom Laptop holen:
cd ~/Documents/PI-Installer
git pull origin main
```

---

## 📝 Spezifische Aufgaben-Aufteilung

### Dokumentationsdateien (Pi-Verantwortung)

Diese Dateien werden primär auf dem **Pi** verwaltet:

- `README.md` - Hauptdokumentation
- `PLAN.md` - Projektplanung
- `ARCHITECTURE.md` - Architektur-Dokumentation
- `FEATURES.md` - Feature-Liste
- `*.plan.md` - Spezifische Pläne (in `.cursor/plans/`)
- `CHANGELOG.md` - Änderungsprotokoll
- `VERSION` - Versionsnummer
- `docs/` - Dokumentations-Ordner (falls vorhanden)

**Workflow:**
```bash
# Auf dem PI:
cd ~/Documents/PI-Installer
nano PLAN.md  # Planung aktualisieren
git add PLAN.md
git commit -m "docs: Planungs-Updates für Feature X"
git push origin main
```

### Code-Dateien (Laptop-Verantwortung)

Diese Dateien werden primär auf dem **Laptop** entwickelt:

- `frontend/src/` - React-Komponenten
- `backend/modules/` - Python-Module
- `backend/app.py` - Hauptanwendung
- `*.tsx`, `*.ts` - TypeScript-Dateien
- `*.py` - Python-Dateien
- `package.json`, `requirements.txt` - Dependencies

**Workflow:**
```bash
# Auf dem LAPTOP:
cd ~/Documents/PI-Installer-Laptop
# Mit Cursor AI entwickeln...
git add frontend/src/components/NewComponent.tsx
git commit -m "feat: Neue Komponente hinzugefügt"
git push origin main
```

---

## 🤖 Automatisierung: Scripts für einfachen Workflow

### Script auf dem Laptop: `sync-to-pi.sh`

Erstelle `~/Documents/PI-Installer-Laptop/sync-to-pi.sh`:

```bash
#!/bin/bash
# Synchronisiert Code-Änderungen zum Pi

echo "🔄 Synchronisiere Code-Änderungen zum Pi..."

# Lokale Änderungen committen (falls vorhanden)
if [[ -n $(git status -s) ]]; then
    echo "📝 Lokale Änderungen gefunden..."
    read -p "Commit-Nachricht eingeben: " commit_msg
    git add .
    git commit -m "$commit_msg"
fi

# Auf GitHub pushen
echo "⬆️  Pushe auf GitHub..."
git push origin main

# Auf dem Pi pullen (optional, falls SSH verfügbar)
echo "⬇️  Aktualisiere Pi-Repository..."
ssh pi "cd ~/Documents/PI-Installer && git pull origin main"

echo "✅ Synchronisation abgeschlossen!"
```

Ausführbar machen:
```bash
chmod +x sync-to-pi.sh
```

### Script auf dem Pi: `update-docs.sh`

Erstelle `~/Documents/PI-Installer/update-docs.sh`:

```bash
#!/bin/bash
# Aktualisiert Dokumentation und pusht auf GitHub

echo "📚 Dokumentations-Update..."

# Neueste Änderungen vom GitHub holen
echo "⬇️  Hole neueste Änderungen..."
git pull origin main

# Dokumentationsdateien auflisten
echo ""
echo "Verfügbare Dokumentationsdateien:"
ls -1 *.md PLAN.md ARCHITECTURE.md FEATURES.md 2>/dev/null

# Nach Änderungen fragen
read -p "Welche Datei möchtest du bearbeiten? (Enter für Skip): " doc_file

if [[ -n "$doc_file" ]]; then
    nano "$doc_file"
    
    # Änderungen committen
    read -p "Commit-Nachricht: " commit_msg
    git add "$doc_file"
    git commit -m "docs: $commit_msg"
    
    # Auf GitHub pushen
    echo "⬆️  Pushe auf GitHub..."
    git push origin main
    echo "✅ Dokumentation aktualisiert!"
else
    echo "⏭️  Übersprungen."
fi
```

Ausführbar machen:
```bash
chmod +x update-docs.sh
```

---

## 🎯 Best Practices

### 1. Klare Commit-Messages

**Auf dem Laptop (Code):**
```bash
git commit -m "feat: Neue Backup-Funktion hinzugefügt"
git commit -m "fix: Bug in User-Management behoben"
git commit -m "refactor: Code-Struktur optimiert"
```

**Auf dem Pi (Dokumentation):**
```bash
git commit -m "docs: Planungs-Updates für Backup-Feature"
git commit -m "docs: Architektur-Diagramm aktualisiert"
git commit -m "docs: Changelog für Version 1.1.0"
```

### 2. Regelmäßige Synchronisation

**Täglich:**
- Laptop: `git pull` vor Beginn der Arbeit
- Pi: `git pull` vor Dokumentations-Updates
- Beide: `git push` nach Änderungen

**Wöchentlich:**
- Vollständige Synchronisation beider Repositories
- Merge-Konflikte auflösen
- Backup des Repositories

### 3. Branch-Strategie

```bash
# Feature-Branches auf dem Laptop
git checkout -b feature/backup-scheduling
# Entwickeln...
git push origin feature/backup-scheduling

# Dokumentations-Branches auf dem Pi (optional)
git checkout -b docs/architecture-update
# Dokumentation aktualisieren...
git push origin docs/architecture-update
```

### 4. Konflikt-Vermeidung

- **Code-Dateien** nur auf dem Laptop bearbeiten
- **Dokumentationsdateien** primär auf dem Pi bearbeiten
- Bei Überschneidungen: Kommunikation vor Änderungen
- Regelmäßig `git pull` vor größeren Änderungen

---

## 🔍 Nützliche Git-Befehle

### Auf dem Laptop

```bash
# Status prüfen
git status

# Neueste Änderungen vom Pi/GitHub holen
git pull origin main

# Eigene Änderungen pushen
git push origin main

# Branch erstellen für Feature
git checkout -b feature/neue-funktion

# Branch auf GitHub pushen
git push -u origin feature/neue-funktion
```

### Auf dem Pi

```bash
# Dokumentations-Status prüfen
git status

# Neueste Code-Änderungen vom Laptop holen
git pull origin main

# Dokumentations-Änderungen pushen
git push origin main

# Änderungen der letzten 7 Tage anzeigen
git log --since="7 days ago" --oneline

# Wer hat was geändert?
git log --author="PI-Dokumentation" --oneline
```

---

## 🚀 Schnellstart-Checkliste

### Erste Einrichtung

- [ ] SSH-Status auf dem Pi prüfen (falls noch nicht aktiv: `sudo systemctl status ssh`)
- [ ] IP-Adresse/Hostname des Pi notieren (`hostname -I` oder `pi5-gg.local`)
- [ ] SSH-Key vom Laptop auf den Pi kopieren (`ssh-copy-id`)
- [ ] SSH-Config auf dem Laptop einrichten (`~/.ssh/config`)
- [ ] SSH-Verbindung testen (`ssh pi`)
- [ ] Repository auf dem Laptop klonen
- [ ] Repository auf dem Pi klonen (oder bereits vorhanden)
- [ ] Git-Config auf beiden Systemen einrichten
- [ ] Sync-Scripts testen
- [ ] Erste Synchronisation testen

### Täglicher Workflow

**Morgens:**
- [ ] Laptop: `git pull` → Neueste Dokumentation vom Pi
- [ ] Pi: `git pull` → Neueste Code-Änderungen vom Laptop

**Während der Arbeit:**
- [ ] Laptop: Code entwickeln, committen, pushen
- [ ] Pi: Dokumentation aktualisieren, committen, pushen

**Abends:**
- [ ] Beide: Finale Synchronisation (`git pull` + `git push`)

---

## 🆘 Troubleshooting

### Problem: Merge-Konflikte

```bash
# Konflikte anzeigen
git status

# Konflikt-Dateien bearbeiten
nano KONFLIKT-DATEI.md

# Nach Bearbeitung:
git add KONFLIKT-DATEI.md
git commit -m "fix: Merge-Konflikt aufgelöst"
git push origin main
```

### Problem: SSH-Verbindung schlägt fehl

```bash
# Verbindung testen (verbose für Details)
ssh -v pi

# SSH-Key neu kopieren (mit explizitem Key-Pfad)
ssh-copy-id -i ~/.ssh/id_ed25519.pub pi@pi5-gg.local
# oder: ssh-copy-id -i ~/.ssh/id_rsa.pub pi@pi5-gg.local

# SSH-Config prüfen
cat ~/.ssh/config

# Prüfe welche Keys vorhanden sind
ls -la ~/.ssh/id_*
```

### Problem: Welcher SSH-Key wird verwendet?

```bash
# Zeige alle vorhandenen Keys
ls -la ~/.ssh/id_*.pub

# Zeige Inhalt eines Keys (erste Zeile zeigt Typ)
cat ~/.ssh/id_ed25519.pub
# Ausgabe: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... (ed25519)
# oder: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAA... (RSA)

# Teste Verbindung mit explizitem Key
ssh -i ~/.ssh/id_ed25519 pi@pi5-gg.local
```

### Problem: Mehrere SSH-Keys vorhanden

Wenn du mehrere Keys hast und einen spezifischen verwenden möchtest:

```bash
# 1. Zeige alle Keys
ls -la ~/.ssh/id_*.pub

# 2. Kopiere den gewünschten Key auf den Pi
ssh-copy-id -i ~/.ssh/id_ed25519.pub pi@pi5-gg.local

# 3. In SSH-Config den richtigen Key angeben
nano ~/.ssh/config
# Füge hinzu:
# IdentityFile ~/.ssh/id_ed25519  # oder welcher Key auch immer
```

### Problem: Git-Push schlägt fehl

```bash
# Neueste Änderungen holen
git pull origin main --rebase

# Erneut pushen
git push origin main
```

---

## 📊 Workflow-Diagramm

```
┌─────────────────┐         ┌─────────────────┐
│     LAPTOP      │         │  RASPBERRY PI   │
│                 │         │                 │
│ • Code-Entw.    │◄───Git──►│ • Dokumentation │
│ • Cursor AI     │         │ • Planung      │
│ • Build/Test    │         │ • Versionierung│
│                 │         │                 │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │                           │
         └───────────┬───────────────┘
                     │
                     ▼
              ┌──────────────┐
              │   GitHub     │
              │  Repository  │
              └──────────────┘
```

---

## 💡 Tipps & Tricks

1. **Git Aliases für schnelleren Workflow:**
   ```bash
   git config --global alias.sync '!git pull origin main && git push origin main'
   git config --global alias.doc '!git add *.md && git commit -m "docs: Update" && git push'
   ```

2. **Automatische Synchronisation:**
   - Cron-Job auf dem Pi für regelmäßige `git pull`
   - Git-Hooks für automatische Dokumentations-Updates

3. **Backup-Strategie:**
   - Regelmäßige Backups des Git-Repositories
   - Lokale Backups auf beiden Systemen

4. **Dokumentations-Templates:**
   - Vorlagen für Planungsdateien auf dem Pi
   - Konsistente Struktur für alle Dokumentation

---

**Version:** 1.0.0  
**Letztes Update:** Februar 2026  
**Autor:** PI-Installer Team
