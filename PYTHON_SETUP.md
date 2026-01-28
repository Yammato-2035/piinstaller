# 🐍 Python Setup Guide für Raspberry Pi

## ⚠️ WICHTIG: Python Version!

PI-Installer funktioniert **nur mit Python 3.12** auf Raspberry Pi!

❌ **Python 3.13** - Nicht unterstützt (PyO3 Fehler)
❌ **Python 3.11 oder älter** - Zu alt
✅ **Python 3.12** - EMPFOHLEN & GETESTET

---

## 🔍 Aktuelle Python Version prüfen

```bash
python3 --version
```

### Ergebnis interpretieren:

**✅ Python 3.12.x**
```
Python 3.12.1
→ PERFEKT! Sie können direkt starten
```

**❌ Python 3.13.x**
```
Python 3.13.0
→ Nicht unterstützt! Folgen Sie der Anleitung unten
```

**❌ Python 3.11.x oder älter**
```
Python 3.11.0
→ Zu alt! Folgen Sie der Anleitung unten
```

---

## 🛠️ Python 3.12 installieren / upgraden

### Für Raspberry Pi OS (Debian 12)

#### Option 1: Auf neuere Raspberry Pi OS Version upgraden

```bash
# Aktuelle Version checken
lsb_release -a

# Auf Debian 12 upgraden (wenn noch nicht)
sudo apt update
sudo apt upgrade -y
```

Dann Python 3.12 installieren:

```bash
sudo apt install -y python3.12 python3.12-venv python3.12-dev
```

#### Option 2: Python 3.12 aus Source kompilieren

Falls Python 3.12 nicht im Repository verfügbar ist:

```bash
# Dependencies installieren
sudo apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnsl-dev \
    zlib1g-dev \
    libreadline-dev \
    liblzma-dev \
    sqlite3 \
    libsqlite3-dev \
    tk-dev \
    uuid-dev

# Python 3.12 downloaden und kompilieren
cd /tmp
wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz
tar xzf Python-3.12.3.tgz
cd Python-3.12.3

# Kompilieren (dauert 30-60 Minuten!)
./configure --enable-optimizations
make -j4
sudo make altinstall

# Prüfen
/usr/local/bin/python3.12 --version
```

#### Option 3: Einfachste Alternative - Python 3.12 via deadsnakes PPA

```bash
# PPA hinzufügen
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa

# Aktualisieren und installieren
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Prüfen
python3.12 --version
```

---

## 📋 Nach Installation prüfen

```bash
# Verfügbare Python Versionen anzeigen
ls /usr/bin/python*

# Python 3.12 Status
python3.12 --version
python3.12 -m venv --help  # Sollte funktionieren
```

**Ausgabe sollte sein:**
```
/usr/bin/python3.12
Python 3.12.3
```

---

## 🚀 PI-Installer mit Python 3.12 starten

### Wichtig: Verwenden Sie `python3.12` statt `python3`!

```bash
cd ~/Documents/PI-Installer/backend

# RICHTIG - Mit expliziter Version
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3.12 app.py

# FALSCH - Könnte falsche Python Version nutzen!
# python3 -m venv venv
# python3 app.py
```

---

## ✅ Korrekte Startup-Befehle

### Terminal 1: Backend mit Python 3.12

```bash
cd ~/Documents/PI-Installer/backend

# Virtual Environment erstellen
python3.12 -m venv venv

# Aktivieren
source venv/bin/activate

# pip aktualisieren
pip install --upgrade pip setuptools wheel

# Dependencies installieren
pip install -r requirements.txt

# Server starten
python3.12 app.py
```

### Terminal 2: Frontend (Node.js)

```bash
cd ~/Documents/PI-Installer/frontend
npm install
npm run dev
```

### Browser öffnen
```
http://localhost:3000
```

---

## 🐛 Wenn Sie immer noch Python 3.13 haben

### Schnelle Workaround (NICHT empfohlen):

```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install -r requirements.txt
```

⚠️ **ABER:** Das ist nicht stabil. Besser Python 3.12 verwenden!

---

## 🔄 Virtual Environment neu erstellen

Falls Sie vorher eine erstellt haben:

```bash
cd ~/Documents/PI-Installer/backend

# Alte venv löschen
rm -rf venv

# Mit Python 3.12 neu erstellen
python3.12 -m venv venv

# Aktivieren
source venv/bin/activate

# Dependencies neu installieren
pip install --upgrade pip
pip install -r requirements.txt

# Testen
python3.12 app.py
```

---

## 📊 Kompatibilität Matrix

| Python | Status | Empfehlung |
|--------|--------|-----------|
| 3.9 | ⚠️ Alt | Nicht empfohlen |
| 3.10 | ⚠️ Alt | Nicht empfohlen |
| 3.11 | ⚠️ Alt | Funktioniert, nicht optimal |
| **3.12** | ✅ IDEAL | **VERWENDEN SIE DIESE** |
| 3.13 | ❌ Nicht unterstützt | Noch nicht reif für Raspberry Pi |

---

## 🎯 Debian Version Check

Prüfen Sie auch Ihre Debian Version:

```bash
lsb_release -a
cat /etc/debian_version
```

**Idealerweise:**
- Debian 12 (Bookworm)
- Raspberry Pi OS Latest

---

## ⚡ Schnelle Zusammenfassung

| Schritt | Befehl |
|--------|--------|
| 1. Prüfe Version | `python3.12 --version` |
| 2. Gehe zu Projekt | `cd ~/Documents/PI-Installer/backend` |
| 3. Erstelle venv | `python3.12 -m venv venv` |
| 4. Aktiviere venv | `source venv/bin/activate` |
| 5. Update pip | `pip install --upgrade pip` |
| 6. Install deps | `pip install -r requirements.txt` |
| 7. Starte Server | `python3.12 app.py` |

---

## 🆘 Immer noch Fehler?

### Fehler: `python3.12: command not found`

```bash
# Python 3.12 ist nicht installiert
# Folgen Sie obiger Anleitung zur Installation
sudo apt install -y python3.12 python3.12-venv python3.12-dev
```

### Fehler: `PYO3` Build Error

```bash
# Sie verwenden wahrscheinlich Python 3.13
python3 --version  # Check!

# Lösung: Python 3.12 verwenden
python3.12 -m venv venv
source venv/bin/activate
python3.12 -m pip install -r requirements.txt
```

### Fehler: `ModuleNotFoundError`

```bash
# Sie sind wahrscheinlich nicht in venv
source venv/bin/activate
which python3  # Sollte ...venv/bin/python3 zeigen
pip install -r requirements.txt
```

---

## 🎉 Erfolgskriterien

**Installation erfolgreich wenn:**
```bash
python3.12 --version
# → Python 3.12.x

python3.12 -m venv test_venv
# → Kein Fehler

pip install pydantic==2.8.0
# → Erfolgreich installiert (keine Build-Fehler)
```

---

## 🔗 Weitere Ressourcen

- [Raspberry Pi Python Docs](https://www.raspberrypi.com/documentation/computers/os.html)
- [Python.org](https://www.python.org/downloads/)
- [PyO3 Docs](https://pyo3.rs/)

---

**Version:** 1.0.0  
**Datum:** 2026-01-24  
**Status:** ✅ Python 3.12 empfohlen
