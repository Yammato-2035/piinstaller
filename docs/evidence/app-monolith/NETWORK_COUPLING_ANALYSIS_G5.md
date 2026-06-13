# Network Coupling Analysis — G.5

**HEAD:** `307c411`

## 1. `get_system_info` (`GET /api/system-info`)

**Ort:** `app.py` Z.6322–6562 (~240 Zeilen)  
**Network-Anteil:** 3 Zeilen (Z.6554–6556) — Facade-only ✓

### Nicht-Network-Abhängigkeiten

| Bereich | Technik | Helfer |
|---------|---------|--------|
| CPU/Memory/Disk | `psutil` | inline |
| Temperatur/Lüfter | sysfs, `get_cpu_temp`, `get_fan_speed` | app helpers |
| OS/Kernel | `/etc/os-release`, `uname -r` | `run_command` |
| Hardware/Pi | `_get_pi_config_module`, DMI, device-tree | app helpers |
| GPU/PCI | `lspci`, `nvidia-smi`, `_get_gpus_for_system_info` | app helpers |
| Sensoren/Disks | `get_all_thermal_sensors`, `get_all_disks`, … | app helpers |
| Demo-Mode | `_is_demo_mode` | app |

### Auslagerbarkeit

| Teil | Auslagerbar? | Neues Modul? |
|------|--------------|--------------|
| `network`-Block | ja (bereits Facade) | — |
| psutil-Aggregation | ja, groß | **System Info Facade** (G.6) |
| Hardware/Pi-Erkennung | teilweise | System Info Facade + bestehende Pi-Module |
| Sensoren/Disks/PCI | ja | System Info Facade oder `hardware_info_facade` |
| `light=True` Polling-Pfad | ja | System Info Facade (gleiche API) |

**Blocker G.4:** Gesamthandler zu groß für reinen Network-Router — G.6 sinnvoller nächster Schritt.

### Frontend-Kopplung

- `App.tsx`, `Dashboard.tsx`, `MonitoringDashboard.tsx`, `InstallationWizard.tsx`
- Polling mit `?light=1` — Response-Contract darf nicht brechen

---

## 2. `webserver_status` (`GET /api/webserver/status`)

**Ort:** `app.py` Z.8500–8581 (~82 Zeilen)

### Abhängigkeiten

| Bereich | Technik | Owner heute |
|---------|---------|-------------|
| Network-Info | `build_network_info()` | **network_info_facade** ✓ |
| Frontend-Port | `_detect_frontend_port()` | **app.py direkt** ✗ |
| Services | `get_running_services()` | app (`systemctl is-active`) |
| Ports | `run_command("ss -tuln …")` | app |
| Apps/CMS | `get_installed_apps()`, `check_installed` | app |
| Websites | `get_website_names()` | app (nginx/apache config parse) |

### Auslagerbarkeit

| Teil | Auslagerbar? | Neues Modul? |
|------|--------------|--------------|
| Gesamtpayload | ja | **Webserver Status Facade** (G.7) |
| Network-Teil | bereits Facade | — |
| Port-Erkennung | ja | **Port Detection / Frontend Runtime Facade** |
| Service-Probes | ja | Webserver Facade (delegiert an Service-Helper) |
| `ss`-Port-Scan | ja | Webserver Facade |

**Direkt-Bypass:** `_detect_frontend_port()` in Handler — vor G.7 auf Facade-API umstellen.

### Frontend-Kopplung

- `WebServerSetup.tsx` — erwartet vollständiges JSON inkl. `pi_installer`, `nginx`, `network`, CMS

---

## 3. Zyklische Facade ↔ app-Kopplung

```
HTTP → network_info_facade → import app → get_network_info() → run_command/subprocess
```

**Problem:** Facade ist kanonischer Owner, aber Implementierung lebt im Monolith.  
**Elimination-Pfad:** Discovery-Implementierung nach `core/network_discovery.py` verschieben; Facade ruft Core statt `app`.

---

## 4. Port-Erkennung (Querschnitt)

| Verbraucher | Zugriff |
|-------------|---------|
| `build_system_network_response` | `_legacy_detect_frontend_port` ✓ |
| `webserver_status` | `_detect_frontend_port()` direkt ✗ |

**Empfehlung:** Öffentliche Facade-API `detect_frontend_port()` oder separates Port-Modul; beide Verbraucher darüber.

---

## 5. Was kann später sauber ausgelagert werden?

| Slice | Aufwand | Router-Extraktion danach? |
|-------|---------|---------------------------|
| Network Discovery (`get_network_info`) | mittel | entlastet Facade-Adapter |
| Port Detection | niedrig | ja, für webserver + system/network |
| System Info (ohne network) | hoch | `GET /api/system-info` → eigener Router |
| Webserver Status | mittel | `GET /api/webserver/status` → Router G.7+ |

## 6. Was benötigt neue Facades?

| Facade | Begründung |
|--------|------------|
| **System Info** (G.6) | psutil/Hardware-Monolith; größter verbleibender GET-Handler |
| **Webserver Status** (G.7) | Service/`ss`/CMS-Aggregation; G.4-blockiert |
| **Frontend Runtime / Port** | `_detect_frontend_port` + künftige Dev/Build-Port-Logik |
| **Network Discovery** (optional G.8) | Legacy-Elimination ohne API-Änderung |

**Nicht nötig:** Erweiterung von `network_info_facade` um psutil/Systeminfo — verstößt gegen G.1/G.2-Grenzen.
