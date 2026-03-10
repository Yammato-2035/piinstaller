# Backend Modules – Verantwortlichkeiten

_Phase 4 – Strukturelle Systemvereinfachung_

## Aktiv genutzte Module

| Modul | Verwendung in app.py | Zuständigkeit |
|-------|---------------------|---------------|
| **raspberry_pi_config** | `_get_pi_config_module()` – Raspberry-Pi-Konfiguration, Overlays, EDID, Audio, Display | Hardware- und Low-Level-Konfiguration |
| **backup** | `_get_backup_module()` – Backup-/Restore-Logik | Backup-Jobs, Verifizierung |
| **control_center** | `_get_control_center_module()` – WLAN, SSH, VNC, Telemetrie, OLED, Lüfter | Systemeinstellungen, Peripherie |

---

## Nicht von app.py genutzte Module (STRUCTURE-MANUAL-REVIEW)

| Modul | Status | Hinweis |
|-------|--------|---------|
| **security** | Nicht genutzt | Logik lebt inline in app.py; Endpunkte direkt in app.py |
| **webserver** | Nicht genutzt | Logik lebt inline in app.py |
| **mail** | Nicht genutzt | Backend hat TODO für `/api/mail/configure`; Modul nicht eingebunden |
| **devenv** | Nicht genutzt | Backend hat TODO für `/api/devenv/configure`; Modul nicht eingebunden |
| **users** | Nur über __init__ | User-Logik teils in app.py; Modul-Struktur existiert |

**Entfernung:** Nur nach manueller Prüfung und Klärung, ob externe Referenzen (z.B. CONFIG.md) bestehen.

---

## Abhängigkeiten

- Alle Module nutzen `SystemUtils` aus `utils.py`
- `control_center` importiert intern `raspberry_pi_config`
- Lade-Mechanismus: Lazy `_get_*_module()` in app.py
