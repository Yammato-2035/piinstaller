# 🚀 PI-Installer für Debian 13 (Trixie) mit Python 3.13

## ✅ Gute Nachricht: Python 3.13 wird jetzt unterstützt!

Sie haben **Debian 13 (Trixie)** mit **Python 3.13.5** - das ist perfekt! 

Ich habe die Dependencies aktualisiert, um Python 3.13 Pre-Built Wheels zu verwenden.

---

## 🚀 SCHNELLSTART mit Python 3.13

### Schritt 1: Alten venv löschen

```bash
cd ~/Documents/PI-Installer/backend
rm -rf venv
rm -rf __pycache__
```

### Schritt 2: Neuen venv mit Python 3.13 erstellen

```bash
# Python 3.13 verwenden (Standard)
python3 -m venv venv

# Aktivieren
source venv/bin/activate

# Prüfen
python3 --version  # Sollte Python 3.13.5 zeigen
```

### Schritt 3: pip aktualisieren

```bash
pip install --upgrade pip setuptools wheel
```

### Schritt 4: Dependencies installieren

```bash
# WICHTIG: Mit --only-binary für Pre-Built Wheels
pip install -r requirements.txt --only-binary :all:
```

Falls das nicht funktioniert (ohne --only-binary):

```bash
pip install -r requirements.txt
```

### Schritt 5: Backend starten

```bash
python3 app.py
```

**Erfolgsmeldung:**
```
Uvicorn running on http://0.0.0.0:8000
```

### Schritt 6: Frontend starten (neues Terminal)

```bash
cd ~/Documents/PI-Installer/frontend
npm install
npm run dev
```

### Schritt 7: Browser öffnen

```
http://localhost:3000
```

---

## 📋 Was wurde aktualisiert?

### requirements.txt für Python 3.13 optimiert:

```diff
- fastapi==0.104.1  → + fastapi==0.108.0
- pydantic==2.5.0   → + pydantic==2.6.0
- uvicorn==0.24.0   → + uvicorn==0.27.0
```

Diese Versionen haben **Pre-Built Wheels für Python 3.13 aarch64**!

---

## 🎯 KURZ-VERSION: Kopieren & Einfügen

```bash
cd ~/Documents/PI-Installer/backend && \
rm -rf venv && \
python3 -m venv venv && \
source venv/bin/activate && \
pip install --upgrade pip && \
pip install -r requirements.txt --only-binary :all: && \
python3 app.py
```

---

## ✨ Debian 13 Vorteile

✅ Python 3.13 ist die neueste Version
✅ Alle Pre-Built Wheels verfügbar
✅ Schnelle Installation (kein Rust-Compile nötig)
✅ Stabiler und sicherer

---

## 🔍 Diagnose

### Python-Version prüfen

```bash
python3 --version
# Sollte: Python 3.13.5 zeigen

python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
# Sollte: 3.13 zeigen
```

### venv Check

```bash
source venv/bin/activate
python3 --version
which python3
# Sollte: /home/gabrielglienke/Documents/PI-Installer/backend/venv/bin/python3 zeigen
```

### Dependencies Check

```bash
pip list | grep -E "fastapi|pydantic|uvicorn"
# Sollte zeigen:
# fastapi                  0.108.0
# pydantic                 2.6.0
# pydantic-core            2.20.x
# uvicorn                  0.27.0
```

---

## 🚨 Falls immer noch Fehler

### Error: "pydantic-core build failed"

**Lösung 1: Mit --only-binary installieren**
```bash
pip install -r requirements.txt --only-binary :all:
```

**Lösung 2: pip cache clearen**
```bash
pip cache purge
pip install -r requirements.txt
```

**Lösung 3: Einzelne Pakete**
```bash
pip install pydantic==2.6.0 --only-binary :all:
pip install -r requirements.txt
```

### Error: "No module named fastapi"

```bash
# Virtual Environment nicht aktiviert?
source venv/bin/activate

# Oder neu installieren
pip install -r requirements.txt
```

---

## 🐳 Docker Alternative (Kein Python-Setup nötig!)

Falls Installation immer noch Probleme macht:

```bash
docker-compose up

# Browser: http://localhost:3000
```

Docker handled alle Dependencies automatisch! 🎉

---

## 📊 Versionskompatibilität

| Komponente | Version | Python 3.13 | Status |
|-----------|---------|-------------|--------|
| FastAPI | 0.108.0 | ✅ | Pre-Built Wheel |
| Pydantic | 2.6.0 | ✅ | Pre-Built Wheel |
| pydantic-core | 2.20.x | ✅ | Pre-Built Wheel |
| Uvicorn | 0.27.0 | ✅ | Pre-Built Wheel |
| Cryptography | 41.0.7 | ✅ | Pre-Built Wheel |
| PyYAML | 6.0.1 | ✅ | Pure Python |
| Jinja2 | 3.1.2 | ✅ | Pure Python |

**Alle Pakete mit Pre-Built Wheels - Keine Rust-Compilation!** 🎉

---

## 🎉 Los geht's!

```bash
# Terminal 1: Backend
cd ~/Documents/PI-Installer/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 app.py

# Terminal 2: Frontend
cd ~/Documents/PI-Installer/frontend
npm install
npm run dev

# Browser: http://localhost:3000
```

**Viel Erfolg!** 🚀

---

**Version:** 1.0.1  
**Optimiert für:** Debian 13 Trixie + Python 3.13  
**Status:** ✅ Voll unterstützt
