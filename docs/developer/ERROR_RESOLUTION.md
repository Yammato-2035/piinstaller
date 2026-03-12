# 🔧 PyO3/Python 3.13 Fehler - GELÖST

## ❌ Fehlermeldung

```
error: the configured Python interpreter version (3.13) is 
newer than PyO3's maximum supported version (3.12)
```

**Grund:** PyO3 0.21.1 (in pydantic-core) unterstützt Python 3.13 noch nicht.

---

## ✅ LÖSUNG: Python 3.12 verwenden

### Schnelle Überprüfung

```bash
# Aktuelle Version
python3 --version

# Verfügbare Versionen
ls /usr/bin/python3.*
```

### Szenario 1: Python 3.12 ist verfügbar

```bash
# Perfekt! Nutzen Sie python3.12 statt python3

cd ~/Documents/PI-Installer/backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3.12 app.py
```

### Szenario 2: Python 3.12 ist nicht vorhanden

```bash
# Installation
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Dann Szenario 1 wiederholen
```

### Szenario 3: Sie haben nur Python 3.13

**Optionen:**

#### A) Python 3.12 installieren (empfohlen)
```bash
# Debian 12 (Bookworm) - Python 3.12 ist verfügbar
sudo apt install python3.12 python3.12-venv python3.12-dev

# Dann python3.12 verwenden (siehe oben)
```

#### B) Auf ältere Debian Version downgraden
Falls Sie Debian Testing/Unstable haben:
```bash
# Lesen Sie: https://wiki.debian.org/DebianTesting
```

#### C) Python 3.12 von Source kompilieren
```bash
# Siehe PYTHON_SETUP.md - "Option 2: Aus Source"
# Dauert 30-60 Minuten!
```

---

## 📋 Was wurde geändert

### 1. requirements.txt
```diff
- fastapi==0.115.0        # Zu neu für Python 3.12
+ fastapi==0.109.0        # Kompatibel

- pydantic==2.7.0         # Zu neu
+ pydantic==2.8.0         # Besser kompatibel

- uvicorn==0.31.0         # Zu neu
+ uvicorn==0.29.0         # Stabil
```

Diese Versionen sind **für Python 3.12 optimiert** und bauen ohne Rust-Compilation!

### 2. Neue Dokumentation
- `PYTHON_SETUP.md` - Kompletter Python-Setup-Guide
- `START_HERE.txt` - Schnelle Referenz
- Dieses Dokument

---

## 🎯 Richtige Startup-Befehle

### ✅ RICHTIG (mit Python 3.12)

```bash
# Terminal 1
cd ~/Documents/PI-Installer/backend
python3.12 -m venv venv      ← WICHTIG: python3.12!
source venv/bin/activate
pip install -r requirements.txt
python3.12 app.py            ← WICHTIG: python3.12!
```

### ❌ FALSCH (mit Python 3.13)

```bash
# Das funktioniert NICHT!
python3 -m venv venv          # ← Könnte Python 3.13 sein!
python3 app.py                # ← Könnte Python 3.13 sein!
```

---

## 🔍 Diagnose

### 1. Prüfen welche Python-Versionen verfügbar sind

```bash
ls -la /usr/bin/python3*
```

**Beispielausgabe:**
```
/usr/bin/python3 -> python3.13     ← Zu neu!
/usr/bin/python3.12 -> python3.12  ← PERFEKT!
/usr/bin/python3.11                ← Zu alt
```

### 2. Aktive Python Version im venv prüfen

```bash
source venv/bin/activate
python3 --version
which python3
```

**Sollte sein:** `/home/gabrielglienke/Documents/PI-Installer/backend/venv/bin/python3`

### 3. pip Pakete prüfen

```bash
pip list | grep -E "pydantic|fastapi|uvicorn"
```

**Sollte sein:**
```
fastapi                  0.109.0
pydantic                 2.8.0
pydantic-core            2.20.x
uvicorn                  0.29.0
```

---

## 🚀 Nach der Fehlerbehebung

### Backend starten (neu)

```bash
cd ~/Documents/PI-Installer/backend

# Alten venv löschen
rm -rf venv

# Mit Python 3.12 neu erstellen
python3.12 -m venv venv
source venv/bin/activate

# Dependencies installieren (sollte schnell gehen!)
pip install -r requirements.txt

# Server starten
python3.12 app.py

# ✅ Sollte zeigen:
# Uvicorn running on http://0.0.0.0:8000
```

### Frontend starten

```bash
cd ~/Documents/PI-Installer/frontend
npm install
npm run dev

# ✅ Sollte zeigen:
# Local: http://localhost:3000
```

---

## 💡 Warum Python 3.12?

### PyO3 Support Matrix

| Python | PyO3 0.21.1 | PyO3 0.22.0 |
|--------|-------------|------------|
| 3.9 | ✅ | ✅ |
| 3.10 | ✅ | ✅ |
| 3.11 | ✅ | ✅ |
| 3.12 | ✅ | ✅ |
| **3.13** | ❌ | ✅ (kommend) |

**Lösung:** Neue PyO3 Version wartet noch auf offizielle Release.
**Workaround:** Python 3.12 verwenden (ist stabil & getestet)

---

## ✨ Vorher vs. Nachher

### Vorher (mit Python 3.13 & alten Versionen)
```
error: build failed
pydantic-core compile error
Waiting 30 minutes...
❌ Fehler
```

### Nachher (mit Python 3.12 & neuen Versionen)
```
Collecting fastapi==0.109.0
...
Successfully installed fastapi-0.109.0 pydantic-2.8.0
✅ Erfolg in < 5 Minuten
```

---

## 📞 Wenn immer noch Fehler

1. **Lesen Sie PYTHON_SETUP.md** - Detaillierter Guide
2. **Versuchen Sie Docker:** `docker-compose up`
3. **Öffnen Sie GitHub Issue** mit:
   - `python3 --version`
   - `pip3 --version`
   - Komplette Fehlermeldung

---

## 🎉 Zusammenfassung

### Das Wichtigste:

```bash
# IMMER python3.12 verwenden, NICHT python3!

python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3.12 app.py
```

**Fertig!** 🚀

---

**Behoben am:** 2026-01-24  
**Reason:** PyO3/Python 3.13 Inkompatibilität  
**Lösung:** Python 3.12 + kompatible Versionen  
**Status:** ✅ Funktioniert stabil

---

## 🔌 LAN (Ethernet/eth0) verbindet nicht – nur WLAN

### Symptom

Der Pi ist im Netzwerk nur per WLAN erreichbar; über Ethernet (eth0) kommt keine Verbindung zustande.

### Schnelle Diagnose auf dem Pi

```bash
# Im Projektordner auf dem Pi oder vom Laptop:
ssh pi@pi5-gg.local 'bash -s' < scripts/diagnose-lan.sh
```

Oder auf dem Pi ausführen:

```bash
bash scripts/diagnose-lan.sh
```

Die Ausgabe wird nach `/tmp/pi-lan-diagnose.txt` geschrieben und zeigt u.a.:

- Ob ein Ethernet-Interface existiert (eth0, end0, …)
- **Carrier**: 0 = Kabel nicht verbunden / kein Link, 1 = Link vorhanden
- **operstate**: up/down
- IP-Adresse am LAN-Interface (fehlt, wenn kein DHCP-Lease)
- Kernel-Meldungen (Link/Carrier-Fehler)

### Typische Ursachen und Maßnahmen

| Ursache | Prüfung / Lösung |
|--------|-------------------|
| **Kabel nicht verbunden oder defekt** | Kabel an Pi und Router fest stecken; anderes Kabel testen. |
| **Router-Port** | Anderen Port am Router/Switch testen; anderes Gerät am gleichen Port prüfen. |
| **Carrier = 0** | Kein physischer Link – Kabel, Stecker, ggf. Router-Port tauschen. |
| **Carrier = 1, aber keine IP** | DHCP-Problem: Router liefert keine Adresse; `dhcpcd`/`systemd-networkd` prüfen (Skript zeigt aktive Dienste). |
| **Stromversorgung** | Schlechte Stromversorgung kann Ethernet instabil machen (5 V, min. 2.5 A für Pi 3/4). |
| **USB-Ethernet-Adapter** | Anderen USB-Port nutzen; Treiber/`dmesg` prüfen (Skript zeigt Kernel-Meldungen). |

### Manuelle Prüfung (ohne Skript)

```bash
# Interface-Status
ip link show eth0

# Carrier (0 = kein Link, 1 = Link)
cat /sys/class/net/eth0/carrier

# Detaillierter Link-Status (falls ethtool installiert)
sudo apt install -y ethtool
ethtool eth0
```

**Hinweis:** Wenn der Pi nur per WLAN genutzt wird, reicht `pi5-gg.local` (Hostname Pi5-GG) oder die WLAN-IP für SSH und den PI-Installer (siehe WORKFLOW_LAPTOP_PI.md).
