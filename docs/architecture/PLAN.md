# PI-Installer - Entwicklungsplan

**Erstellt:** 2026-01-27  
**Status:** In Planung  
**Version:** v1.1 → v2.0

---

## 🎯 Aktuelle Prioritäten

### Phase 1: Fehlende Core-Funktionalitäten (Hoch)

#### 1.1 TODO-Implementierungen im Backend
- [ ] **Devenv Configure Endpoint** (`backend/app.py:3695`)
  - Konfigurations-Endpoint für Entwicklungsumgebung implementieren
  - Integration in InstallationWizard
  - Validierung der Konfigurationsparameter
  
- [ ] **Mailserver Configure Endpoint** (`backend/app.py:3758`)
  - Konfigurations-Endpoint für Mailserver implementieren
  - Domain/DNS-Validierung
  - TLS/SSL-Setup-Integration
  - Spam-Filter-Konfiguration

#### 1.2 Backup & Restore System
- [ ] **Backend-Modul erstellen** (`backend/modules/backup.py`)
  - Automatische Backup-Funktionalität
  - Incremental Backups
  - Backup-Verifizierung
  - Restore-Funktionalität
  
- [ ] **Frontend-Seite erweitern** (`frontend/src/pages/BackupRestore.tsx`)
  - Backup-Planung GUI
  - Backup-Historie anzeigen
  - Restore-Wizard
  - Cloud-Integration (S3, Google Cloud)

#### 1.3 Monitoring & Dashboard
- [ ] **System-Monitoring Backend** (`backend/modules/monitoring.py`)
  - CPU/Memory/Disk-Metriken sammeln
  - Service-Status überwachen
  - Alert-System implementieren
  
- [ ] **Monitoring Dashboard** (`frontend/src/pages/MonitoringDashboard.tsx`)
  - Real-time Metriken anzeigen
  - Grafische Visualisierung
  - Alert-Konfiguration
  - Log-Viewer Integration

---

### Phase 2: Wichtige Erweiterungen (Mittel)

#### 2.1 VPN-Setup (WireGuard)
- [ ] **Backend-Modul** (`backend/modules/vpn.py`)
  - WireGuard Installation & Konfiguration
  - QR-Code-Generierung für Clients
  - Client-Management
  - Port-Forwarding-Assistent
  
- [ ] **Frontend-Seite** (`frontend/src/pages/VPNSetup.tsx`)
  - VPN-Konfigurations-Wizard
  - Client-Verwaltung
  - Status-Anzeige

#### 2.2 Database Management Tools
- [ ] **PhpMyAdmin Integration**
  - Automatische Installation
  - Konfiguration für MySQL/MariaDB
  - Sicherheits-Härtung
  
- [ ] **pgAdmin Integration**
  - Automatische Installation
  - Konfiguration für PostgreSQL
  - Verbindungs-Management

#### 2.3 Cron-Job Manager
- [ ] **Backend-Modul** (`backend/modules/cron.py`)
  - Cron-Job CRUD-Operationen
  - Validierung von Cron-Syntax
  - Log-Management
  
- [ ] **Frontend-Seite** (`frontend/src/pages/CronManager.tsx`)
  - GUI für Cron-Job-Verwaltung
  - Template-Bibliothek
  - Ausführungs-Historie

---

### Phase 3: System-Optimierungen (Mittel)

#### 3.1 System-Basis-Konfiguration
- [ ] **System-Modul erweitern** (`backend/modules/system.py`)
  - Static IP-Konfiguration
  - Hostname-Änderung
  - DNS-Server-Konfiguration
  - Timezone-Einstellung
  - Locale-Konfiguration
  
- [ ] **Frontend-Integration**
  - System-Einstellungsseite erweitern
  - Netzwerk-Konfigurations-Wizard

#### 3.2 Performance-Optimierungen
- [ ] **Backend**
  - WebSocket-Support für Live-Updates
  - Caching-Strategien verbessern
  - Database Query Optimization
  
- [ ] **Frontend**
  - Code Splitting implementieren
  - Lazy Loading für Seiten
  - Image Compression

---

### Phase 4: Erweiterte Features (Niedrig)

#### 4.1 Container Management
- [ ] **Portainer Integration**
  - Automatische Installation
  - Docker-Management-Interface
  
- [ ] **Kubernetes Support (k3s)**
  - k3s Installation
  - Cluster-Management

#### 4.2 CI/CD Integration
- [ ] **GitLab Runner Setup**
  - Automatische Installation
  - Konfigurations-Assistent
  
- [ ] **GitHub Actions Runner**
  - Self-Hosted Runner Setup
  - Konfigurations-Management

#### 4.3 IoT & Smart Home
- [ ] **Home Assistant Integration**
  - Automatische Installation
  - Konfigurations-Assistent
  
- [ ] **MQTT Broker Setup**
  - Mosquitto Installation
  - Konfigurations-Interface

---

## 📋 Technische Schulden

### Code-Qualität
- [ ] **TypeScript vollständig implementieren**
  - Alle `.tsx` Dateien vollständig typisiert
  - Strict Mode aktivieren
  
- [ ] **Testing Framework**
  - Jest für Unit-Tests (Frontend)
  - Pytest für Backend-Tests
  - Cypress für E2E-Tests

### Dokumentation
- [ ] **API-Dokumentation erweitern**
  - Swagger/OpenAPI vollständig dokumentieren
  - Beispiel-Requests hinzufügen
  
- [ ] **Code-Kommentare**
  - Komplexe Funktionen dokumentieren
  - Type Hints im Backend vervollständigen

### Sicherheit
- [ ] **Security Audit**
  - Dependency-Vulnerabilities prüfen
  - Code-Security-Scan durchführen
  - Penetration-Testing vorbereiten

---

## 🗓️ Zeitplan (Geschätzt)

### Q1 2026 (Januar-März)
- ✅ Phase 1.1: TODO-Implementierungen (2-3 Wochen)
- ✅ Phase 1.2: Backup & Restore (3-4 Wochen)
- ✅ Phase 1.3: Monitoring Dashboard (2-3 Wochen)

### Q2 2026 (April-Juni)
- ✅ Phase 2.1: VPN-Setup (2 Wochen)
- ✅ Phase 2.2: Database Tools (2-3 Wochen)
- ✅ Phase 2.3: Cron-Job Manager (1-2 Wochen)
- ✅ Phase 3.1: System-Basis-Konfiguration (2 Wochen)

### Q3 2026 (Juli-September)
- ✅ Phase 3.2: Performance-Optimierungen (2-3 Wochen)
- ✅ Phase 4.1: Container Management (3-4 Wochen)
- ✅ Testing & Bug-Fixes (laufend)

### Q4 2026 (Oktober-Dezember)
- ✅ Phase 4.2: CI/CD Integration (2-3 Wochen)
- ✅ Phase 4.3: IoT & Smart Home (3-4 Wochen)
- ✅ Dokumentation & Release-Vorbereitung

---

## 🎯 Nächste Schritte (Diese Woche)

### Sofort (Priorität 1)
1. **Devenv Configure Endpoint implementieren**
   - Datei: `backend/app.py`
   - Endpoint: `/api/devenv/configure`
   - Integration in InstallationWizard

2. **Mailserver Configure Endpoint implementieren**
   - Datei: `backend/app.py`
   - Endpoint: `/api/mailserver/configure`
   - Domain-Validierung hinzufügen

### Diese Woche (Priorität 2)
3. **Backup-Modul erstellen**
   - Neue Datei: `backend/modules/backup.py`
   - Basis-Funktionalität implementieren
   - API-Endpoints erstellen

4. **Monitoring-Backend erweitern**
   - Datei: `backend/modules/monitoring.py` (neu)
   - Metriken-Sammlung implementieren
   - API-Endpoints für Dashboard

### Nächste Woche (Priorität 3)
5. **Backup-Restore Frontend erweitern**
   - Datei: `frontend/src/pages/BackupRestore.tsx`
   - GUI für Backup-Planung
   - Restore-Wizard

6. **Monitoring Dashboard Frontend**
   - Datei: `frontend/src/pages/MonitoringDashboard.tsx`
   - Real-time Metriken-Anzeige
   - Grafische Visualisierung

---

## 📊 Fortschritts-Tracking

### Implementiert (v1.0)
- ✅ Sicherheit & Härtung
- ✅ Benutzerverwaltung
- ✅ Entwicklungsumgebung (Installation)
- ✅ Webserver
- ✅ Mailserver (Installation)
- ✅ Frontend & GUI

### In Arbeit (v1.1)
- 🔄 Devenv Configure Endpoint
- 🔄 Mailserver Configure Endpoint
- 🔄 Backup & Restore System

### Geplant (v2.0)
- ⏳ Monitoring & Logging
- ⏳ VPN Setup
- ⏳ Database Management Tools
- ⏳ Cron-Job Manager
- ⏳ System-Optimierungen

---

## 🔄 Review & Anpassung

**Nächste Review:** Wöchentlich  
**Verantwortlich:** Entwicklungsteam  
**Feedback:** GitHub Issues & Pull Requests

---

## 📝 Notizen

- Alle neuen Features sollten vollständig dokumentiert werden
- Backward-Kompatibilität bei API-Änderungen beachten
- Security-Best-Practices bei allen neuen Features einhalten
- Performance-Tests für neue Features durchführen

---

**Letzte Aktualisierung:** 2026-01-27
