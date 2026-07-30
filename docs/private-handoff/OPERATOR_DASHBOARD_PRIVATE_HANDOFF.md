# Operator Dashboard — Private Handoff

**Klassifizierung:** PROPRIETARY · **Nur privates Repository**  
**Stand:** 2026-06-16

---

## 1. Zweck

Übergabe für **Operator Dashboard** — zentrale UI und APIs für Betrieb, Kundenübersicht, Lizenzstatus und Korrelation von Telemetrie/Diagnostik. **Keine** Implementierung im Public-Repository.

---

## 2. Scope

| Feature | Beschreibung |
|---------|--------------|
| Fleet-/Installations-Übersicht | Pseudonyme IDs, keine Klartext-PII in Listen |
| Telemetrie-Aggregate | Read-only aus privatem Telemetry Server |
| Diagnose-Sessions | Read-only aus privatem Diagnostics Server |
| Lizenz / Billing | Feature-Flags, Quota — nur privat |
| Benachrichtigungen | Spiegel von `NOTIFICATION_EVENT_CONTRACT` (operator-sichtbar) |
| Deploy/Runtime-Alerts | Integration mit privatem Monitoring |

---

## 3. Verboten im Public-Repo

Gate blockiert u. a.:

- `backend/operator_dashboard/`
- `frontend/src/pages/CloudOperatorDashboard.tsx`
- `frontend/src/operator/`
- Marker `OPERATOR_DASHBOARD` in Implementierungskontext

Public enthält nur dieses Handoff und ggf. **read-only DCC** für Entwickler (`dev_dashboard`).

---

## 4. Abhängigkeiten (Private)

```text
operator_private  →  telemetry_server (read)
                  →  diagnostics_server (read)
                  →  license/billing modules
                  →  audit_event_contract (Anzeige)
                  →  notification_event_contract (Spiegel)
```

---

## 5. UI-Anforderungen

- [ ] Rollenbasierter Zugriff (RBAC)
- [ ] Keine Secrets in Browser-Storage
- [ ] Session-Timeout und MFA (Betriebspolicy)
- [ ] Audit-Log für Operator-Aktionen
- [ ] Trennung Staging/Production

Beispiel-API-Host (Doku): `https://operator.internal.setuphelfer.example`

---

## 6. Datenklassifikation

| Daten | Speicherort | Anzeige im Dashboard |
|-------|-------------|----------------------|
| Kunden-E-Mail | Billing (privat) | Maskiert |
| Installations-Telemetrie | Telemetry Server | Aggregiert |
| Rescue-Evidence | Kunden-local / optional Upload | Nur mit Consent |

---

## 7. Abnahmekriterien

- [ ] Kein Code-Leak in Public-PRs (Boundary-Gate)
- [ ] Pen-Test Operator-Auth
- [ ] TOM-Dokument aktualisiert
- [ ] Beta nur mit NDA + Beta-Agreement (siehe Legal)

---

## 8. Verfügbare Public-Contract-Felder für Hardware-/Treiberanzeige

`backend/core/rescue_system_assessment_v2.py` (`system-assessment.v2`, öffentlich, read-only) liefert seit dieser Erweiterung zusätzlich:

| Feld | Beschreibung |
|------|--------------|
| `mainboard.board_vendor` / `mainboard.board_name` | Mainboard-Hersteller/-Modell (DMI) |
| `mainboard.bios_vendor` / `mainboard.bios_version` / `mainboard.bios_release_date` | BIOS-Informationen (DMI) |
| `cpu_ram.cpu_vendor_display` | Normalisiert: `Intel` / `AMD` / `unknown` |
| `gpu.integrated_graphics_present` / `gpu.discrete_graphics_present` | Grafikeinheit(en) vorhanden |
| `gpu.vendors` | GPU-Hersteller (`intel`/`amd`/`nvidia`) |
| `gpu.vendor_driver_gaps` | Hersteller ohne gebundenen Kernel-Treiber (Treiberbedarf-Signal) |
| `issue_codes` | u. a. `bios_info_unavailable`, `cpu_info_partial`, `gpu_driver_missing`, `nvidia_compat_mode` |
| `recommendation_codes` | u. a. `review_gpu_driver_coverage` (plan-only) |

Das private Operator-Dashboard kann diese Felder aus dem Assessment-Bundle (`rescue.master_assessment_bundle.v1` bzw. der Telemetrie-Payload aus `rescue_assessment_telemetry_v1.py`) übernehmen, statt eigene Hardware-Erkennung zu implementieren. Alle Werte sind bereits durch `redact_assessment_payload()` gelaufen.

---

## 9. Referenzen

- [`SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md`](../architecture/SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md)
- [`NOTIFICATION_EVENT_CONTRACT.md`](../architecture/NOTIFICATION_EVENT_CONTRACT.md)
- [`OPERATOR_DASHBOARD_PRIVATE_HANDOFF.md`](OPERATOR_DASHBOARD_PRIVATE_HANDOFF.md) (dieses Dokument)
