# Rescue Fleet Agent Contract (Stub v1)

Status: **Contract definiert, Stub implementiert, nicht produktiv**.

## Agent Identity (Pflicht)

- `agent_id`, `agent_kind=rescue_stick`, `agent_version`, `boot_id`, `session_id`
- `device_identity.machine_id_hash`, `dmi_vendor`, `dmi_product`, `serial_hash=null`
- `privacy.no_plain_serials=true`, `privacy.no_plain_ip_persistence=true`, `privacy.operator_consent_required=true`

## System Report (Pflicht)

- Schema: `1.0`, Metadaten, OS/Hardware/Netzwerk/Storage/Boot/Safety/Evidence
- Kein Klartext-Serial, keine persistierte Klartext-IP, kein Geolocation-Autofill
- `site_hint` nur operator-gesteuert

## Gating und Sichtbarkeit

- Dashboard-Anzeige nur bei gültiger Pairing-/Session-Lage
- Release-Profil blockiert Registrierung standardmäßig
- Nur Stub-Routen, keine Write/Apply/Execute-Pfade

## Noch nicht produktiv

- Vollständige Hardware-Erfassung im Live-System
- Produktive E2EE-Kryptobibliothek
- Live-ISO/USB-Lauf
